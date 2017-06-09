import os
import time
import queue
import re
import threading
import copy
from collections import OrderedDict
import requests
import lxml.html
import multiprocessing

from .helpers import color_logging
from .url_queue import UrlQueue
from . import helpers


def parse_seeds(seeds):
    """ parse website seeds.
    @params
        seeds example:
            - url1
            - user1:pwd1@url1
            - user1:pwd1@url1|url2|user3:pwd3@url3
    """
    seeds = seeds.strip().split('|')
    website_list = []
    for seed in seeds:
        if '@' not in seed:
            website = {
                'url': seed,
                'auth': None
            }
        else:
            user_pwd, url = seed.split('@')
            username, password = user_pwd.split(':')
            website = {
                'url': url,
                'auth': (username, password)
            }

        website_list.append(website)

    return website_list

def _make_url_by_referer(origin_parsed_obj, referer_url):
    """
    @params
        referer_url: e.g. https://store.debugtalk.com/product/osmo
        origin_parsed_obj.path e.g.:
            (1) complete urls: http(s)://store.debugtalk.com/product/phantom-4-pro
            (2) cdn asset files: //asset1.xcdn.com/assets/xxx.png
            (3) relative links type1: /category/phantom
            (4) relative links type2: mavic-pro
            (5) relative links type3: ../compare-phantom-3
    @return
        corresponding result url:
            (1) http(s)://store.debugtalk.com/product/phantom-4-pro
            (2) http://asset1.xcdn.com/assets/xxx.png
            (3) https://store.debugtalk.com/category/phantom
            (4) https://store.debugtalk.com/product/mavic-pro
            (5) https://store.debugtalk.com/compare-phantom-3
    """
    if origin_parsed_obj.scheme != "":
        # complete urls, e.g. http(s)://store.debugtalk.com/product/phantom-4-pro
        return origin_parsed_obj

    elif origin_parsed_obj.netloc != "":
        # cdn asset files, e.g. //asset1.xcdn.com/assets/xxx.png
        origin_parsed_obj = origin_parsed_obj._replace(scheme='http')
        return origin_parsed_obj

    elif origin_parsed_obj.path.startswith('/'):
        # relative links, e.g. /category/phantom
        referer_url_parsed_object = helpers.get_parsed_object_from_url(referer_url)
        origin_parsed_obj = origin_parsed_obj._replace(
            scheme=referer_url_parsed_object.scheme,
            netloc=referer_url_parsed_object.netloc
        )
        return origin_parsed_obj
    else:
        referer_url_parsed_object = helpers.get_parsed_object_from_url(referer_url)
        path_list = referer_url_parsed_object.path.split('/')

        if origin_parsed_obj.path.startswith('../'):
            # relative links, e.g. ../compare-phantom-3
            path_list.pop()
            path_list[-1] = origin_parsed_obj.path.lstrip('../')
        else:
            # relative links, e.g. mavic-pro
            path_list[-1] = origin_parsed_obj.path

        new_path = '/'.join(path_list)
        origin_parsed_obj = origin_parsed_obj._replace(path=new_path)

        origin_parsed_obj = origin_parsed_obj._replace(
            scheme=referer_url_parsed_object.scheme,
            netloc=referer_url_parsed_object.netloc
        )
        return origin_parsed_obj


class WebCrawler(object):

    def __init__(self, seeds, include_hosts, logs_folder):
        self.website_list = parse_seeds(seeds)
        self.include_hosts_set = set(include_hosts)
        self.test_counter = 0
        self.url_queue = UrlQueue()
        self.cookie_str = ''
        self.auth_dict = {}
        self.logs_folder = logs_folder
        for website in self.website_list:
            website_url = website['url']
            host = helpers.get_parsed_object_from_url(website_url).netloc
            self.include_hosts_set.add(host)
            if website['auth']:
                self.auth_dict[host] = website['auth']

        self.load_config()
        self.categorised_urls = {}
        self.web_urls_mapping = {}
        self.bad_urls_mapping = {}
        self.current_depth_unvisited_urls_queue = queue.Queue()

    def reset_all(self):
        self.current_depth = 0
        self.current_depth_unvisited_urls_queue.queue.clear()
        self.url_queue.clear_unvisited_urls()

        for website in self.website_list:
            website_url = website['url']
            self.url_queue.remove_visited_url(website_url)
            self.url_queue.add_unvisited_url(website_url)

    def load_config(self):
        self.kwargs = {
            'headers': {},
            'cookies': {}
        }
        config_file = os.path.join(os.path.dirname(__file__), 'config.yml')
        config_dict = helpers.load_yaml_file(config_file)
        self.url_type_config = config_dict['Content-Type']
        headers = config_dict['headers']
        self.user_agent = headers['User-Agent']
        self.kwargs['timeout'] = config_dict['default_timeout']
        self.whitelist_host = config_dict['whitelist-host']
        self.whitelist_url = config_dict['whitelist-url']
        self.whitelist_key = config_dict['whitelist-key']
        self.whitelist_startswith = config_dict['whitelist-startswith']
        self.grey_env = False

    def set_grey_env(self, user_agent, traceid, view_grey):
        self.kwargs['headers']['User-Agent'] = user_agent
        self.kwargs['cookies']['traceid'] = traceid
        self.kwargs['cookies']['view_grey'] = view_grey
        self.grey_env = True
        self.grey_user_agent = user_agent

    def get_user_agent_by_url(self, url):
        if '//m.' in url:
            # e.g. http://m.debugtalk.com
            return self.user_agent['mobile']
        else:
            return self.user_agent['www']

    def parse_url(self, url, referer_url):
        url = url.strip()
        if url == "":
            return None

        for ignore_url_startswith_str in self.whitelist_startswith:
            if url.startswith(ignore_url_startswith_str):
                return None

        if url.startswith('\\"'):
            # \\"https:\\/\\/store.debugtalk.com\\/guides\\/"
            url = url.encode('utf-8').decode('unicode_escape')\
                .replace(r'\/', r'/').replace(r'"', r'')
            return url

        parsed_object = helpers.get_parsed_object_from_url(url)

        # remove url fragment
        parsed_object = parsed_object._replace(fragment='')
        parsed_object = _make_url_by_referer(parsed_object, referer_url)

        return parsed_object.geturl()

    def get_url_type(self, resp, req_host):
        try:
            content_type = resp.headers['Content-Type']
        except KeyError:
            url_type = 'IGNORE'
            return url_type

        if content_type in self.url_type_config['static']:
            url_type = 'static'
        elif req_host not in self.include_hosts_set:
            url_type = 'external'
        else:
            url_type = 'recursive'
        return url_type

    def parse_urls(self, urls_set, referer_url):
        parsed_urls_set = set()
        for url in urls_set:
            parsed_url = self.parse_url(url, referer_url)
            if parsed_url is None:
                continue
            parsed_urls_set.add(parsed_url)
        return parsed_urls_set

    def parse_page_links(self, referer_url, content):
        """ parse a web pages and get all hyper links.
        """
        raw_links_set = set()

        try:
            etree = lxml.html.fromstring(content)
        except lxml.etree.ParserError:
            return raw_links_set

        link_elements_list = etree.xpath("//link|//a|//script|//img")
        for link in link_elements_list:
            url = link.get('href') or link.get('src')
            if url is None:
                continue
            raw_links_set.add(url)

        parsed_urls_set = self.parse_urls(raw_links_set, referer_url)
        return parsed_urls_set

    def save_categorised_url(self, status_code, url):
        """ save url by status_code category
        """
        if status_code not in self.categorised_urls:
            self.categorised_urls[status_code] = set()

        self.categorised_urls[status_code].add(url)

    def _print_log(self, depth, url, status_code, duration_time):
        self.test_counter += 1
        color_logging(
            "test_counter: {}, depth: {}, url: {}, cookie: {}, status_code: {}, duration_time: {}s"
            .format(self.test_counter, depth, url, self.cookie_str, status_code, round(duration_time, 3)), 'DEBUG')

    def is_url_has_whitelist_key(self, url):
        for key in self.whitelist_key:
            if key in url:
                return True

        return False

    def get_hyper_links(self, url, depth, retry_times=3):
        if url in self.whitelist_url:
            return set()

        hyper_links_set = set()
        kwargs = copy.deepcopy(self.kwargs)
        if not self.grey_env:
            kwargs['headers']['User-Agent'] = self.get_user_agent_by_url(url)
        parsed_object = helpers.get_parsed_object_from_url(url)
        url_host = parsed_object.netloc
        if url_host in self.whitelist_host:
            return set()
        if self.is_url_has_whitelist_key(url):
            return set()
        if url_host in self.auth_dict and self.auth_dict[url_host]:
            kwargs['auth'] = self.auth_dict[url_host]

        exception_str = ""
        status_code = '0'
        resp_content_md5 = None
        duration_time = 0
        try:
            start_time = time.time()
            resp = requests.head(url, **kwargs)
            url_type = self.get_url_type(resp, url_host)
            if url_type in ['static', 'external']:
                if resp.status_code in [301, 302]:
                    start_time = time.time()
                    resp = requests.get(url, **kwargs)
                duration_time = time.time() - start_time
                status_code = str(resp.status_code)
            elif url_type == 'IGNORE':
                duration_time = time.time() - start_time
                status_code = str(resp.status_code)
                retry_times = 0
            else:
                # recursive
                start_time = time.time()
                resp = requests.get(url, **kwargs)
                duration_time = time.time() - start_time
                resp_content_md5 = helpers.get_md5(resp.content)
                hyper_links_set = self.parse_page_links(resp.url, resp.content)
                if url not in self.web_urls_mapping:
                    self.web_urls_mapping[url] = list(hyper_links_set)
                status_code = str(resp.status_code)
                self.url_queue.add_unvisited_urls(hyper_links_set)
                if resp.status_code > 400:
                    exception_str = 'HTTP Status Code is {}.'.format(status_code)
        except requests.exceptions.SSLError as ex:
            color_logging("{}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'SSLError'
            retry_times = 0
        except requests.exceptions.ConnectionError as ex:
            color_logging("ConnectionError {}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'ConnectionError'
        except requests.exceptions.Timeout:
            time_out = kwargs['timeout']
            color_logging("Timeout {}: Timed out for {} seconds".format(url, time_out), 'WARNING')
            exception_str = "Timed out for {} seconds".format(time_out)
            status_code = 'Timeout'
        except requests.exceptions.InvalidSchema as ex:
            color_logging("{}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'InvalidSchema'
            retry_times = 0
        except requests.exceptions.ChunkedEncodingError as ex:
            color_logging("{}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'ChunkedEncodingError'
            retry_times = 0
        except requests.exceptions.InvalidURL as ex:
            color_logging("{}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'InvalidURL'
            retry_times = 0
        except lxml.etree.XMLSyntaxError as ex:
            color_logging("{}: {}".format(url, str(ex)), 'WARNING')
            exception_str = str(ex)
            status_code = 'XMLSyntaxError'
            retry_times = 0

        self._print_log(depth, url, status_code, duration_time)
        if retry_times > 0:
            if not status_code.isdigit() or int(status_code) > 400:
                time.sleep((4-retry_times)*2)
                return self.get_hyper_links(url, depth, retry_times-1)
        else:
            self.bad_urls_mapping[url] = exception_str

        self.save_categorised_url(status_code, url)
        url_test_res = {
            'status_code': status_code,
            'duration_time': duration_time,
            'md5': resp_content_md5
        }
        self.url_queue.add_visited_url(url, url_test_res)
        return hyper_links_set

    def get_referer_urls_set(self, url):
        """ get all referer urls of the specified url.
        """
        referer_set = set()
        for parent_url, hyper_links_set in self.web_urls_mapping.items():
            if url in hyper_links_set:
                referer_set.add(parent_url)
        return referer_set

    def get_sorted_categorised_urls(self):
        return OrderedDict(
            sorted(self.categorised_urls.items(), reverse=True)
        ).items()

    def print_categorised_urls(self):

        def _print(status_code, urls_list, log_level, show_referer=False):
            if isinstance(status_code, str):
                output = "{}: {}.\n".format(status_code, len(urls_list))
            elif isinstance(status_code, int):
                output = "HTTP status code {}, total: {}.\n".format(status_code, len(urls_list))

            output += "urls list: \n"
            for url in urls_list:
                output += url
                if not str(status_code).isdigit():
                    output += ", {}: {}".format(status_code, self.bad_urls_mapping[url])
                if show_referer:
                    # only show 5 referers if referer urls number is greater than 5
                    referer_urls = self.get_referer_urls_set(url)
                    referer_urls_num = len(referer_urls)
                    if referer_urls_num > 5:
                        referer_urls = list(referer_urls)[:5]
                        output += ", referer_urls: {}".format(referer_urls)
                        output += " total {}, displayed 5.".format(referer_urls_num)
                    else:
                        output += ", referer_urls: {}".format(referer_urls)
                output += '\n'

            color_logging(output, log_level)

        for status_code, urls_list in self.get_sorted_categorised_urls():
            color_logging('-' * 120)
            if status_code.isdigit():
                status_code = int(status_code)
                if status_code >= 500:
                    _print(status_code, urls_list, 'ERROR', True)
                elif status_code >= 400:
                    _print(status_code, urls_list, 'ERROR', True)
                elif status_code >= 300:
                    _print(status_code, urls_list, 'WARNING')
                elif status_code > 200:
                    _print(status_code, urls_list, 'INFO')
            else:
                _print(status_code, urls_list, 'ERROR', True)

    def run_dfs(self, max_depth):
        """ start to run test in DFS mode.
        """
        def crawler(url, depth):
            """ DFS crawler
            """
            if depth > max_depth:
                return

            if self.url_queue.is_url_visited(url):
                urls = set()
            else:
                urls = self.get_hyper_links(url, depth)

            for url in urls:
                crawler(url, depth+1)

        while not self.url_queue.is_unvisited_urls_empty():
            url = self.url_queue.get_one_unvisited_url()
            crawler(url, self.current_depth)

    def run_bfs(self, max_depth):
        """ start to run test in BFS mode.
        """
        while self.current_depth <= max_depth:
            while not self.url_queue.is_unvisited_urls_empty():
                url = self.url_queue.get_one_unvisited_url()
                self.current_depth_unvisited_urls_queue.put_nowait(url)

            self.current_depth_unvisited_urls_queue.join()
            self.current_depth += 1

    def visit_url(self):
        while True:
            try:
                url = self.current_depth_unvisited_urls_queue.get()
                self.get_hyper_links(url, self.current_depth)
            finally:
                self.current_depth_unvisited_urls_queue.task_done()

    def create_threads(self, concurrency):
        for _ in range(concurrency):
            thread = threading.Thread(
                target=self.visit_url,
                args=()
            )
            thread.daemon = True
            thread.start()

    def start(self, cookies={}, crawl_mode='BFS', max_depth=10, concurrency=None):
        """ start to run test in specified crawl_mode.
        @params
            crawl_mode = 'BFS' or 'DFS'
        """
        concurrency = int(concurrency or multiprocessing.cpu_count() * 4)
        info = "Start to run test in {} mode, cookies: {}, max_depth: {}, concurrency: {}"\
            .format(crawl_mode, cookies, max_depth, concurrency)
        color_logging(info)
        self.reset_all()
        self.create_threads(concurrency)

        self.kwargs['cookies'].update(cookies)
        self.cookie_str = '_'.join(['_'.join([key, cookies[key]]) for key in cookies])

        if crawl_mode.upper() == 'BFS':
            self.run_bfs(max_depth)
        else:
            self.run_dfs(max_depth)

        color_logging('=' * 120, color='yellow')

    def print_result(self, canceled=False, save_visited_urls=False):
        status = "Canceled" if canceled else "Finished"
        color_logging("{}. The crawler has tested {} urls."\
            .format(status, self.url_queue.get_visited_urls_count()))
        self.print_categorised_urls()

        if save_visited_urls:
            urls_mapping_log_path = os.path.join(self.logs_folder, 'urls_mapping.yml')
            helpers.save_to_yaml(self.web_urls_mapping, urls_mapping_log_path)
            color_logging("Save urls mapping in YAML file: {}".format(urls_mapping_log_path))
            visited_urls_log_path = os.path.join(self.logs_folder, 'visited_urls.yml')
            helpers.save_to_yaml(self.url_queue.get_visited_urls(), visited_urls_log_path)
            color_logging("Save visited urls in YAML file: {}".format(visited_urls_log_path))

    def gen_mail_content(self, jenkins_log_url):
        website_urls = [website['url'] for website in self.website_list]
        content = "Tested websites: {}<br/>".format(','.join(website_urls))
        content += "Total tested urls number: {}<br/><br/>"\
            .format(self.url_queue.get_visited_urls_count())
        content += "Categorised urls number by HTTP Status Code: <br/>"
        for status_code, urls_list in self.get_sorted_categorised_urls():
            if status_code.isdigit():
                content += "status code {}: {}".format(status_code, len(urls_list))
            else:
                content += "{} urls: {}".format(status_code, len(urls_list))

            content += "<br/>"

        content += "<br/>Detailed Jenkins log info: {}".format(jenkins_log_url)
        mail_content = {
            'type': 'html',
            'content': content
        }
        return mail_content
