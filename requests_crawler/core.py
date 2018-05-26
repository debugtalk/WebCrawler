import logging
import math
import multiprocessing
import queue
import time

import lxml.etree
from requests import adapters, exceptions
from requests_html import HTMLSession, MaxRetries

from termcolor import colored

from . import default_config


def color_logging(text, log_level='info', color=None):
    log_level = log_level.upper()
    if log_level == 'DEBUG':
        color = color or 'blue'
        logging.debug(colored(text, color))
    elif log_level == 'INFO':
        color = color or 'green'
        logging.info(colored(text, color))
    elif log_level == 'WARNING':
        color = color or 'yellow'
        logging.warning(colored(text, color, attrs=['bold']))
    elif log_level == 'ERROR':
        color = color or 'red'
        logging.error(colored(text, color, attrs=['bold']))


class Worker(multiprocessing.Process):

    def __init__(self, unvisited_urls_queue, fetched_urls_queue, result_queue, counter, config):
        multiprocessing.Process.__init__(self)
        self.unvisited_urls_queue = unvisited_urls_queue
        self.fetched_urls_queue = fetched_urls_queue
        self.result_queue = result_queue
        self.counter = counter
        self.config = config
        self.kwargs = config["kwargs"]
        self.session = HTMLSession()

        a = adapters.HTTPAdapter(
            pool_connections = 100,
            pool_maxsize = 100
        )
        self.session.mount("http://", a)
        self.session.mount("https://", a)

    def get_url_type(self, url, resp):

        for include_snippet in self.config["include"]:
            if include_snippet in url:
                content_type = resp.headers.get('Content-Type', None)
                if content_type and "text/html" in content_type:
                    url_type = 'recursive'
                else:
                    url_type = 'static'

                return url_type
            else:
                continue

        return "external"

    def check_url_info(self, url):
        for exclude_snippet in self.config["exclude"]:
            if exclude_snippet in url:
                status_code = None
                url_type = "exclude"
                return (status_code, url_type)

        try:
            resp = self.session.head(url, **self.kwargs)
            status_code = resp.status_code
            url_type = self.get_url_type(url, resp)
        except exceptions.ConnectTimeout as ex:
            color_logging(f"{url}: {str(ex)}", 'WARNING')
            status_code = "ConnectTimeout"
            url_type = None
        except exceptions.ConnectionError as ex:
            color_logging(f"{url}: {str(ex)}", 'WARNING')
            status_code = "ConnectionError"
            url_type = None

        return (status_code, url_type)

    def get_hyper_links(self, url):
        # session.browser
        status_code = None
        hyper_links = set()

        try:
            resp = self.session.get(url, **self.kwargs)
            status_code = resp.status_code
        except exceptions.ConnectionError as ex:
            color_logging(f"{url}: {str(ex)}", 'ERROR')
            status_code = "ConnectionError"

        try:
            resp.html.render(timeout=30)
            hyper_links = resp.html.absolute_links
        except lxml.etree.ParserError as ex:
            color_logging(f"{url}: {str(ex)}", 'ERROR')
        except UnicodeDecodeError as ex:
            color_logging(f"{url}: {str(ex)}", 'ERROR')
        except MaxRetries as ex:
            color_logging(f"{url}: {str(ex)}", 'ERROR')

        return (status_code, hyper_links)

    def run(self):
        while True:
            unvisited_url = self.unvisited_urls_queue.get()
            if unvisited_url is None:
                # Poison pill means shutdown
                color_logging(f'{self.name}: Exiting')
                self.unvisited_urls_queue.task_done()
                break

            start_time = time.time()
            status_code, url_type = self.check_url_info(unvisited_url)

            method = "HEAD"
            if url_type in ["exclude"]:
                color_logging(f"skip url: {unvisited_url}", color="blue")
                self.unvisited_urls_queue.task_done()
                continue
            if url_type in ['static', 'external']:
                hyper_links = set()
            elif url_type in ['recursive']:
                method = "GET & Render"
                status_code, hyper_links = self.get_hyper_links(unvisited_url)
            else:
                # url_type is None
                # TODO: raise exception
                hyper_links = set()

            duration_time = time.time() - start_time
            result = (unvisited_url, status_code, duration_time, hyper_links)
            self.result_queue.put(result)

            for link in hyper_links:
                self.fetched_urls_queue.put(link)

            self.unvisited_urls_queue.task_done()
            self.counter.value += 1

            color_logging(f"index: {self.counter.value}, {method} {unvisited_url}, status_code: {status_code}, duration_time: {duration_time}, worker: {self.name}", color="white")


class RequestsCrawler(object):

    def __init__(self, max_workers=None, requests_limit=None, interval_limit=None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.requests_limit = requests_limit or math.inf
        self.interval_limit = interval_limit or 1
        self.unvisited_urls_queue = multiprocessing.JoinableQueue()
        self.fetched_urls_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.visited_urls_set = set()
        self.counter = multiprocessing.Value('i', 0)
        self.elapsed_time = None

    def _init_workers(self, config):

        def clear_queue(queue):
            while not queue.empty():
                queue.get()

        clear_queue(self.unvisited_urls_queue)
        clear_queue(self.fetched_urls_queue)
        clear_queue(self.result_queue)
        self.visited_urls_set.clear()
        self.counter.value = 0
        self.elapsed_time = None

        # Start workers
        color_logging(f'Creating {self.max_workers} workers', "INFO")
        workers = [
            Worker(self.unvisited_urls_queue, self.fetched_urls_queue, self.result_queue, self.counter, config)
            for i in range(self.max_workers)
        ]

        for w in workers:
            w.daemon = True
            w.start()

        return workers

    def aggregate_results(self):
        """ aggregate url by status_code category
        """
        aggregate_by_status_code = {}
        aggregate_by_url = {}

        while True:
            try:
                url, status_code, duration_time, hyper_links = self.result_queue.get(timeout=5)

                # aggregate status_code
                if status_code not in aggregate_by_status_code:
                    aggregate_by_status_code[status_code] = {}

                aggregate_by_status_code[status_code][url] = duration_time

                # aggregate hyper links
                if url not in aggregate_by_url:
                    aggregate_by_url[url] = {
                        "referers": set(),
                        "hyper_links": set()
                    }
                aggregate_by_url[url]["hyper_links"] = hyper_links

                # aggregate referer
                for link in hyper_links:
                    if link not in aggregate_by_url:
                        aggregate_by_url[link] = {
                            "referers": set(),
                            "hyper_links": set()
                        }

                    aggregate_by_url[link]["referers"].add(url)

            except queue.Empty:
                break

        aggregate_results = {
            "by_status_code": aggregate_by_status_code,
            "by_url": aggregate_by_url
        }

        return aggregate_results

    def print_results(self, aggregate_results, canceled=False, config=None):
        status = "Canceled" if canceled else "Finished"
        config = config or {}
        color_logging('=' * 50 + " aggregate results " + '=' * 50, color='yellow')
        color_logging(f"status: {status}")
        color_logging(f"configuration: {config}")
        color_logging(f"total crawled: {self.counter.value}")
        color_logging(f"total elapsed: {self.elapsed_time}")

        for status_code, data in aggregate_results["by_status_code"].items():
            number = len(data)
            color_logging(f"status_code {status_code}: {number}")

        color_logging('-' * 120, color='white')
        for url, data in aggregate_results["by_url"].items():
            color_logging(f"{url}, referer: {data['referers']}, hyper_links: {data['hyper_links']}")

        color_logging('=' * 120, color='yellow')

    def crawl(self, seed, config):
        self._init_workers(config)
        start_time = time.time()

        # Enqueue jobs
        self.unvisited_urls_queue.put(seed)

        start_timer = time.time()
        requests_queued = 0
        while True:
            self.unvisited_urls_queue.join()

            while True:
                try:
                    url = self.fetched_urls_queue.get(timeout=5)
                except queue.Empty:
                    break

                # visited url will not be crawled twice
                if url in self.visited_urls_set:
                    continue

                # limit rpm
                if requests_queued >= self.requests_limit:
                    runtime_secs = time.time() - start_timer
                    if runtime_secs < self.interval_limit:
                        sleep_secs = self.interval_limit - runtime_secs
                        color_logging(f"exceed {self.requests_limit} per {self.interval_limit} seconds, sleep {sleep_secs} seconds.", "warning")
                        time.sleep(sleep_secs)

                    start_timer = time.time()
                    requests_queued = 0

                self.unvisited_urls_queue.put(url)
                self.visited_urls_set.add(url)
                requests_queued += 1

            if self.unvisited_urls_queue.empty() and self.fetched_urls_queue.empty():
                color_logging("all fetched urls done")
                [self.unvisited_urls_queue.put(None) for _ in range(self.max_workers)]
                break

        # Wait for all of the tasks to finish
        self.unvisited_urls_queue.join()
        self.elapsed_time = time.time() - start_time

    def start(self, seed, headers=None, cookies=None, include=None, exclude=None):
        include = include or set()
        include.add(seed)
        exclude = exclude or set()
        kwargs = {
            'headers': headers or default_config.pc_headers,
            'cookies': cookies or {},
            "timeout": default_config.timeout
        }
        config = {
            "kwargs": kwargs,
            "include": include,
            "exclude": exclude
        }

        canceled = False
        try:
            self.crawl(seed, config)
        except KeyboardInterrupt:
            canceled = True
            color_logging("Canceling...", color='red')
        finally:
            aggregate_results = self.aggregate_results()
            self.print_results(aggregate_results, canceled, config)
