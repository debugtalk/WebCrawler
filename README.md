# requests-crawler

A web crawler based on [requests-html][requests-html], mainly targets for url validation test.

## Features

- based on [requests-html][requests-html], **full JavaScript support!**
- support requests frequency limitation, e.g. rps/rpm
- support crawl with headers and cookies
- include & exclude mechanism
- group visited urls by HTTP status code
- display url's referers and hyper links

## Installation/Upgrade

```bash
$ pip install requests-crawler
```

Only **Python 3.6** is supported.

To ensure the installation or upgrade is successful, you can execute command `requests_crawler -V` to see if you can get the correct version number.

```bash
$ requests_crawler -V
0.5.3
```

## Usage

```text
$ requests_crawler -h
usage: requests_crawler [-h] [-V] [--log-level LOG_LEVEL]
                        [--seed SEED]
                        [--headers [HEADERS [HEADERS ...]]]
                        [--cookies [COOKIES [COOKIES ...]]]
                        [--requests-limit REQUESTS_LIMIT]
                        [--interval-limit INTERVAL_LIMIT]
                        [--include [INCLUDE [INCLUDE ...]]]
                        [--exclude [EXCLUDE [EXCLUDE ...]]]
                        [--workers WORKERS]

A web crawler based on requests-html, mainly targets for url validation test.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show version
  --log-level LOG_LEVEL
                        Specify logging level, default is INFO.
  --seed SEED           Specify crawl seed url
  --headers [HEADERS [HEADERS ...]]
                        Specify headers, e.g. 'User-Agent:iOS/10.3'
  --cookies [COOKIES [COOKIES ...]]
                        Specify cookies, e.g. 'lang=en country:us'
  --requests-limit REQUESTS_LIMIT
                        Specify requests limit for crawler, default rps.
  --interval-limit INTERVAL_LIMIT
                        Specify limit interval, default 1 second.
  --include [INCLUDE [INCLUDE ...]]
                        Urls include the snippets will be crawled recursively.
  --exclude [EXCLUDE [EXCLUDE ...]]
                        Urls include the snippets will be skipped.
  --workers WORKERS     Specify concurrent workers number.
```

## Examples

Basic usage.

```bash
$ requests_crawler --seed http://debugtalk.com
```

Crawl with headers and cookies.

```text
$ requests_crawler --seed http://debugtalk.com --headers User-Agent:iOS/10.3 --cookies lang:en country:us
```

Crawl with 30 rps limitation.

```text
$ requests_crawler --seed http://debugtalk.com --requests-limit 30
```

Crawl with 500 rpm limitation.

```text
$ requests_crawler --seed http://debugtalk.com --requests-limit 500 --interval-limit 60
```

Crawl with extra hosts, e.g. `httprunner.org` will also be crawled recursively.

```text
$ requests_crawler --seed http://debugtalk.com --include httprunner.org
```

Skip excluded url snippets, e.g. urls include `httprunner` will be skipped.

```text
$ requests_crawler --seed http://debugtalk.com --exclude httprunner
```

<!-- ## Logs && Report -->


[requests-html]: https://github.com/kennethreitz/requests-html