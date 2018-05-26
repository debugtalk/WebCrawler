
import sys
import logging
import argparse
from .__about__ import __version__, __description__
from .core import color_logging, RequestsCrawler

# Sanity checking.
try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except AssertionError:
    raise RuntimeError('requests-crawler requires Python 3.6+!')


def main():
    """ parse command line options and run commands.
    """
    parser = argparse.ArgumentParser(description=__description__)

    parser.add_argument(
        '-V', '--version', dest='version', action='store_true',
        help="show version")
    parser.add_argument(
        '--log-level', default='INFO', help="Specify logging level, default is INFO.")
    parser.add_argument(
        '--seed', help="Specify crawl seed url")
    parser.add_argument(
        '--headers', nargs='*', help="Specify headers, e.g. 'User-Agent:iOS/10.3'")
    parser.add_argument(
        '--cookies', nargs='*', help="Specify cookies, e.g. 'lang=en country:us'")
    parser.add_argument(
        '--requests-limit', type=int, help="Specify requests limit for crawler, default rps.")
    parser.add_argument(
        '--interval-limit', type=int, default=1, help="Specify limit interval, default 1 second.")
    parser.add_argument(
        '--include', nargs='*', help="Urls include the snippets will be crawled recursively.")
    parser.add_argument(
        '--exclude', nargs='*', help="Urls include the snippets will be skipped.")
    parser.add_argument(
        '--workers', help="Specify concurrent workers number.")

    args = parser.parse_args()

    if args.version:
        print(f"{__version__}")
        exit(0)

    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)
    color_logging("args: %s" % args)

    main_crawler(args)

def main_crawler(args):

    if not args.seed:
        color_logging("crawl seed not specified!", "ERROR")
        exit(0)

    include = set(args.include or [])
    exclude = set(args.exclude or [])
    headers_list = args.headers or []
    cookies_list = args.cookies or []

    headers = {}
    for header in headers_list:
        split_char = "=" if "=" in header else ":"
        key, value = header.split(split_char)
        headers[key] = value

    cookies = {}
    for cookie in cookies_list:
        split_char = "=" if "=" in cookie else ":"
        key, value = cookie.split(split_char)
        cookies[key] = value

    web_crawler = RequestsCrawler(args.workers, args.requests_limit, args.interval_limit)
    web_crawler.start(args.seed, headers, cookies, include, exclude)
