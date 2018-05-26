__version__ = '0.5.0'

import sys
import logging
import argparse
from .core import color_logging, RequestsCrawler

# Sanity checking.
try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except AssertionError:
    raise RuntimeError('RequestsCrawler requires Python 3.6+!')


def main():
    """ parse command line options and run commands.
    """
    parser = argparse.ArgumentParser(
        description='A web crawler for testing website links validation, based on requests-html.')

    parser.add_argument(
        '-V', '--version', dest='version', action='store_true',
        help="show version")
    parser.add_argument(
        '--log-level', default='INFO', help="Specify logging level, default is INFO.")
    parser.add_argument(
        '--seed', help="Specify crawl seed url")
    parser.add_argument(
        '--include-hosts', nargs='*', help="Specify extra hosts to be crawled.")
    parser.add_argument(
        '--exclude-hosts', nargs='*', help="Specify excluded hosts not to be crawled.")
    parser.add_argument(
        '--headers', nargs='*', help="Specify headers, e.g. 'User-Agent:iOS/10.3'")
    parser.add_argument(
        '--cookies', nargs='*', help="Specify cookies, e.g. 'lang=en country:us'")
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

    include_hosts = set(args.include_hosts or [])
    exclude_hosts = set(args.exclude_hosts or [])
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

    web_crawler = RequestsCrawler(args.workers)
    web_crawler.start(args.seed, headers, cookies, include_hosts, exclude_hosts)
