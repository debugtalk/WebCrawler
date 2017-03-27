__version__ = '0.1.0'

import os
import sys
import logging
import argparse
from .core import WebCrawler
from .mail import send_mail
from .helpers import color_logging

def main():
    """ parse command line options and run commands.
    """
    parser = argparse.ArgumentParser(
        description='A web crawler for testing website links validation.')

    parser.add_argument(
        '--log-level', default='INFO',
        help="Specify logging level, default is INFO.")
    parser.add_argument(
        '--seeds', default='http://debugtalk.com',
        help="Specify crawl seed url(s), several urls can be specified with pipe; \
              if auth needed, seeds can be specified like user1:pwd1@url1|user2:pwd2@url2")
    parser.add_argument(
        '--crawl-mode', default='BFS', help="Specify crawl mode, BFS or DFS.")
    parser.add_argument(
        '--max-depth', default=5, type=int, help="Specify max crawl depth.")
    parser.add_argument(
        '--max-concurrent-workers', default=20, type=int,
        help="Specify max concurrent workers number.")
    parser.add_argument(
        '--job-url', default='0', help="Specify jenkins job url.")
    parser.add_argument(
        '--build-number', default='0', help="Specify jenkins build number.")
    parser.add_argument(
        '--smtp-host-port', help="Specify email SMTP host and port.")
    parser.add_argument(
        '--mailgun-id', help="Specify mailgun api id.")
    parser.add_argument(
        '--mailgun-key', help="Specify mailgun api key.")
    parser.add_argument(
        '--email-auth-username', help="Specify email SMTP auth account.")
    parser.add_argument(
        '--email-auth-password', help="Specify email SMTP auth account.")
    parser.add_argument(
        '--email-recepients', help="Specify email recepients.")

    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)
    color_logging("args: %s" % args)

    main_crawler(args)

def main_crawler(args):
    web_crawler = WebCrawler(args.seeds)
    web_crawler.start(
        args.crawl_mode,
        args.max_depth,
        args.max_concurrent_workers
    )

    job_url = args.job_url
    build_number = args.build_number
    yaml_log_folder = os.path.join(os.getcwd(), "logs", '{}'.format(build_number))
    web_crawler.save_logs(yaml_log_folder)

    jenkins_log_url = "{}/{}/console".format(job_url, build_number)
    mail_content = web_crawler.gen_mail_content(jenkins_log_url)
    send_mail(args, mail_content)
