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


class WebCrawler(object):

    def __init__(self, seeds, include_hosts, logs_folder, config_file=None):
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

        self.load_config(config_file)
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

    def load_config(self, config_file):

        if config_file:
            if not os.path.isabs(config_file):
                config_file = os.path.join(os.getcwd(), config_file)
        else:
            config_file = os.path.join(os.path.dirname(__file__), 'default_config.yml')

        config_dict = helpers.load_yaml_file(config_file)

        self.kwargs = {
            'headers': config_dict.get('headers', {}),
            'cookies': {}
        }

        self.url_type_config = config_dict.get('Content-Type', {})
        self.user_agent = self.kwargs["headers"].get('User-Agent', {})
        self.kwargs['timeout'] = config_dict.get('default_timeout', 20)

        whitelist_configs = config_dict.get('whitelist', {})
        self.whitelist_host = whitelist_configs.get('host', [])
        self.whitelist_fullurls = whitelist_configs.get('fullurl', [])
        self.whitelist_include_keys = whitelist_configs.get('include-key', [])
        self.whitelist_startswith_strs = whitelist_configs.get('startswith', [])

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

        for ignore_url_startswith_str in self.whitelist_startswith_strs:
            if url.startswith(ignore_url_startswith_str):
                return None

        if url.startswith('\\"'):
            # \\"https:\\/\\/store.debugtalk.com\\/guides\\/"
            url = url.encode('utf-8').decode('unicode_escape')\
                .replace(r'\/', r'/').replace(r'"', r'')
            return url

        parsed_url = helpers.make_url_with_referer(url, referer_url)
        return parsed_url

    def get_url_type(self, resp, req_host):
        if req_host not in self.include_hosts_set:
            url_type = 'external'
            return url_type

        content_type = resp.headers.get('Content-Type', None)
        if content_type and content_type in self.url_type_config.get('static', []):
            url_type = 'static'
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
        for key in self.whitelist_include_keys:
            if key in url:
                return True

        return False

    def get_hyper_links(self, url, depth, retry_times=3):
        if url in self.whitelist_fullurls:
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
                if resp.status_code in [301, 302, 404, 500]:
                    # some links can not be visited with HEAD method and will return 404 status code
                    # so we recheck with GET method here.
                    start_time = time.time()
                    resp = requests.get(url, **kwargs)
                duration_time = time.time() - start_time
                status_code = str(resp.status_code)
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
        '''
        Print error URLs been classified by HTTP error code,named as HTTP code error block.
        In HTTP code error block, URLs been classified by HOST.
        URLs defined as the URL of which page contains the error links,instead of error link.
        '''

        def _print(status_code, urls_list, log_level, show_referer=False):
            if isinstance(status_code, str):
                output = "{}: {}.\n".format(status_code, len(urls_list))
            elif isinstance(status_code, int):
                output = "HTTP status code {}, total: {}.\n".format(status_code, len(urls_list))

            host_dict = {}
            for url in urls_list:
                referer_url_list = list(self.get_referer_urls_set(url))
                if referer_url_list and referer_url_list is not []:
                    host_url = referer_url_list[0].split("/")[2]
                else:
                    host_url = "root"

                if host_url in host_dict:#Build {host:[url_list]}
                    temp_list = host_dict[host_url]
                    temp_list.append(url)
                    host_dict[host_url] = temp_list
                else:
                    temp_list = []
                    temp_list.append(url)
                    host_dict[host_url] = temp_list

            output += "urls list: \n"

            for host in host_dict:
                output += "---HOST:    " + host + "\n"
                for url in host_dict[host]:
                    output += url
                    if not str(status_code).isdigit():
                        output += ", {}: {}".format(status_code, self.bad_urls_mapping[url])
                        pass
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
            thread = threading.Thread(target=self.visit_url)
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

    def print_result(self, canceled=False, save_results=False):
        status = "Canceled" if canceled else "Finished"
        color_logging("{}. The crawler has tested {} urls."\
            .format(status, self.url_queue.get_visited_urls_count()))
        self.print_categorised_urls()

        if save_results:
            urls_mapping_log_path = os.path.join(self.logs_folder, 'urls_mapping.yml')
            helpers.save_to_yaml(self.web_urls_mapping, urls_mapping_log_path)
            color_logging("Save urls mapping in YAML file: {}".format(urls_mapping_log_path))
            visited_urls_log_path = os.path.join(self.logs_folder, 'visited_urls.yml')
            helpers.save_to_yaml(self.url_queue.get_visited_urls(), visited_urls_log_path)
            color_logging("Save visited urls in YAML file: {}".format(visited_urls_log_path))

    def get_mail_content_ordered_dict(self):
        website_urls = [website['url'] for website in self.website_list]
        mail_content_ordered_dict = OrderedDict({
            "Tested websites": ','.join(website_urls),
            "Total tested urls number": self.url_queue.get_visited_urls_count(),
            "===== Detailed": "Statistics ====="
        })

        flag_code = 0

        for status_code, urls_list in self.get_sorted_categorised_urls():
            if status_code.isdigit():
                mail_content_ordered_dict["status code {}".format(status_code)] = len(urls_list)
                if int(status_code) > 400:
                    flag_code = 1
            else:
                mail_content_ordered_dict[status_code] = len(urls_list)
                flag_code = 1

        return mail_content_ordered_dict, flag_code
