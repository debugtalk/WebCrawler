# WebCrawler

A simple web crawler, mainly targets for link validation test.

## Features

- based on [requests-html][requests-html], **full JavaScript support!**
- support crawl with headers and cookies
- group visited urls by HTTP status code
- display url's referer and hyper links

## Installation/Upgrade

```bash
$ pip install -U git+https://github.com/debugtalk/WebCrawler.git
```

Only **Python 3.6** is supported.

To ensure the installation or upgrade is successful, you can execute command `webcrawler -V` to see if you can get the correct version number.

```bash
$ webcrawler -V
WebCrawler version: 0.5.0
```

## Usage

```text
$ webcrawler -h
usage: main.py [-h] [-V] [--log-level LOG_LEVEL] [--seed SEED]
               [--include-hosts [INCLUDE_HOSTS [INCLUDE_HOSTS ...]]]
               [--exclude-hosts [EXCLUDE_HOSTS [EXCLUDE_HOSTS ...]]]
               [--headers [HEADERS [HEADERS ...]]]
               [--cookies [COOKIES [COOKIES ...]]] [--workers WORKERS]

A web crawler for testing website links validation, based on requests-html.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show version
  --log-level LOG_LEVEL
                        Specify logging level, default is INFO.
  --seed SEED           Specify crawl seed url
  --include-hosts [INCLUDE_HOSTS [INCLUDE_HOSTS ...]]
                        Specify extra hosts to be crawled.
  --exclude-hosts [EXCLUDE_HOSTS [EXCLUDE_HOSTS ...]]
                        Specify excluded hosts not to be crawled.
  --headers [HEADERS [HEADERS ...]]
                        Specify headers, e.g. 'User-Agent:iOS/10.3'
  --cookies [COOKIES [COOKIES ...]]
                        Specify cookies, e.g. 'lang=en country:us'
  --workers WORKERS     Specify concurrent workers number.
```

## Examples

Basic usage.

```bash
$ webcrawler --seed http://debugtalk.com
```

Crawl with headers and cookies.

```text
$ webcrawler --seeds http://debugtalk.com --headers User-Agent:iOS/10.3 --cookies lang:en country:us
```

[requests-html]: https://github.com/kennethreitz/requests-html