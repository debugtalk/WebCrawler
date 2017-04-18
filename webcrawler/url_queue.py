#encoding=utf-8
import queue

class UniqueQueue(queue.Queue):

    def _init(self, maxsize):
        self.clear()

    def clear(self):
        self.all_items_set = set()
        self.queue = []

    def _put(self, item):
        if item not in self.all_items_set:
            self.all_items_set.add(item)
            self.queue.insert(0, item)

    def _get(self):
        return self.queue.pop()

class UrlQueue(object):
    def __init__(self):
        self._visited_urls_dict = {}
        self._unvisited_urls_queue = UniqueQueue()

    def add_visited_url(self, url, url_test_res):
        if url == "" \
            or url is None \
            or url in self._visited_urls_dict:
            return
        self._visited_urls_dict[url] = url_test_res

    def remove_visited_url(self, url):
        self._visited_urls_dict.pop(url, None)
        if url in self._unvisited_urls_queue.all_items_set:
            self._unvisited_urls_queue.all_items_set.remove(url)

    def clear_unvisited_urls(self):
        self._unvisited_urls_queue.clear()

    def add_unvisited_url(self, url):
        if url == "" \
            or url is None \
            or url in self._visited_urls_dict:
            return
        self._unvisited_urls_queue.put_nowait(url)

    def add_unvisited_urls(self, urls):
        if isinstance(urls, str):
            self.add_unvisited_url(urls)
        if isinstance(urls, (list, set)):
            for url in urls:
                self.add_unvisited_url(url)

    def get_one_unvisited_url(self):
        return self._unvisited_urls_queue.get()

    def get_visited_urls_count(self):
        return len(self._visited_urls_dict)

    def get_visited_urls(self):
        return self._visited_urls_dict

    def get_unvisited_urls_count(self):
        return self._unvisited_urls_queue.qsize()

    def is_url_visited(self, url):
        return url in self._visited_urls_dict

    def is_unvisited_urls_empty(self):
        return self._unvisited_urls_queue.empty()
