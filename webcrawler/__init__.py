__version__ = '0.3.3'

import os
import sys
import logging
import argparse
from .core import WebCrawler
from .helpers import color_logging

# Sanity checking.
try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except AssertionError:
    raise RuntimeError('WebCrawler requires Python 3.6+!')


def main():
    """ parse command line options and run commands.
    """
    parser = argparse.ArgumentParser(
        description='A web crawler for testing website links validation.')

    parser.add_argument(
        '-V', '--version', dest='version', action='store_true',
        help="show version")
    parser.add_argument(
        '--log-level', default='INFO',
        help="Specify logging level, default is INFO.")
    parser.add_argument(
        '--config-file', help="Specify config file path.")
    parser.add_argument(
        '--seeds', default='http://debugtalk.com',
        help="Specify crawl seed url(s), several urls can be specified with pipe; \
              if auth needed, seeds can be specified like user1:pwd1@url1|user2:pwd2@url2")
    parser.add_argument(
        '--include-hosts', help="Specify extra hosts to be crawled.")
    parser.add_argument(
        '--cookies', help="Specify cookies, several cookies can be joined by '|'. \
            e.g. 'lang:en,country:us|lang:zh,country:cn'")
    parser.add_argument(
        '--crawl-mode', default='BFS', help="Specify crawl mode, BFS or DFS.")
    parser.add_argument(
        '--max-depth', default=5, type=int, help="Specify max crawl depth.")
    parser.add_argument(
        '--concurrency', help="Specify concurrent workers number.")

    parser.add_argument(
        '--save-results', default='NO', help="Specify if save results, default is NO.")

    parser.add_argument("--grey-user-agent",
                        help="Specify grey environment header User-Agent.")
    parser.add_argument("--grey-traceid",
                        help="Specify grey environment cookie traceid.")
    parser.add_argument("--grey-view-grey",
                        help="Specify grey environment cookie view_gray.")

    args = parser.parse_args()

    if args.version:
        print("WebCrawler version: {}".format(__version__))
        exit(0)

    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)
    color_logging("args: %s" % args)

    main_crawler(args)

def main_crawler(args):
    include_hosts = args.include_hosts.split(',') if args.include_hosts else []
    cookies_list = args.cookies.split('|') if args.cookies else ['']
    jenkins_build_number = args.jenkins_build_number
    logs_folder = os.path.join(os.getcwd(), "logs", '{}'.format(jenkins_build_number))

    web_crawler = WebCrawler(args.seeds, include_hosts, logs_folder, args.config_file)

    # set grey environment
    if args.grey_user_agent and args.grey_traceid and args.grey_view_grey:
        web_crawler.set_grey_env(args.grey_user_agent, args.grey_traceid, args.grey_view_grey)

    canceled = False
    try:
        for cookies_str in cookies_list:
            cookies_str_list = cookies_str.split(',')
            cookies = {}
            for cookie_str in cookies_str_list:
                if ':' not in cookie_str:
                    continue
                key, value = cookie_str.split(':')
                cookies[key.strip()] = value.strip()

            web_crawler.start(
                cookies,
                args.crawl_mode,
                args.max_depth,
                args.concurrency
            )

    except KeyboardInterrupt:
        canceled = True
        color_logging("Canceling...", color='red')
    finally:
        save_results = False if args.save_results.upper() == "NO" else True
        web_crawler.print_result(canceled, save_results)
