# WebCrawler

A simple web crawler, mainly targets for link validation test.

## Features

- running in BFS or DFS mode
- specify concurrent running workers in BFS mode
- crawl seeds can be set to more than one urls
- support crawl with cookies
- configure hyper links regex, including match type and ignore type
- group visited urls by HTTP status code
- flexible configuration in YAML
- send test result by mail, through SMTP protocol or mailgun service
- cancel jobs

## Installation/Upgrade

```bash
$ pip install -U git+https://github.com/debugtalk/WebCrawler.git#egg=WebCrawler
```

To ensure the installation or upgrade is successful, you can execute command `ate -V` to see if you can get the correct version number.

```bash
$ webcrawler -V
0.2.0
```

## Usage

```text
$ python main.py -h
# same as:
$ webcrawler -h
usage: main.py [-h] [--log-level LOG_LEVEL] [--seeds SEEDS]
               [--include-hosts INCLUDE_HOSTS] [--cookies COOKIES]
               [--crawl-mode CRAWL_MODE] [--max-depth MAX_DEPTH]
               [--concurrency CONCURRENCY] [--job-url JOB_URL]
               [--build-number BUILD_NUMBER] [--smtp-host-port SMTP_HOST_PORT]
               [--mailgun-id MAILGUN_ID] [--mailgun-key MAILGUN_KEY]
               [--email-auth-username EMAIL_AUTH_USERNAME]
               [--email-auth-password EMAIL_AUTH_PASSWORD]
               [--email-recepients EMAIL_RECEPIENTS] [--save-results]
               [--not-save-results]

A web crawler for testing website links validation.

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        Specify logging level, default is INFO.
  --seeds SEEDS         Specify crawl seed url(s), several urls can be
                        specified with pipe; if auth needed, seeds can be
                        specified like user1:pwd1@url1|user2:pwd2@url2
  --include-hosts INCLUDE_HOSTS
                        Specify extra hosts to be crawled.
  --cookies COOKIES     Specify cookies, several cookies can be joined by '|'.
                        e.g. 'lang:en,country:us|lang:zh,country:cn'
  --crawl-mode CRAWL_MODE
                        Specify crawl mode, BFS or DFS.
  --max-depth MAX_DEPTH
                        Specify max crawl depth.
  --concurrency CONCURRENCY
                        Specify concurrent workers number.
  --job-url JOB_URL     Specify jenkins job url.
  --build-number BUILD_NUMBER
                        Specify jenkins build number.
  --smtp-host-port SMTP_HOST_PORT
                        Specify email SMTP host and port.
  --mailgun-id MAILGUN_ID
                        Specify mailgun api id.
  --mailgun-key MAILGUN_KEY
                        Specify mailgun api key.
  --email-auth-username EMAIL_AUTH_USERNAME
                        Specify email SMTP auth account.
  --email-auth-password EMAIL_AUTH_PASSWORD
                        Specify email SMTP auth account.
  --email-recepients EMAIL_RECEPIENTS
                        Specify email recepients.
  --save-results
  --not-save-results
```

## Examples

Crawl in BFS mode with 20 concurrent workers, and set maximum depth to 5.

```bash
$ webcrawler --seeds http://debugtalk.com --crawl-mode bfs --max-depth 5 --concurrency 20
```

Crawl in DFS mode, and set maximum depth to 10.

```bash
$ webcrawler --seeds http://debugtalk.com --crawl-mode dfs --max-depth 10
```

Crawl several websites in BFS mode with 20 concurrent workers, and set maximum depth to 10.

```bash
$ webcrawler --seeds http://debugtalk.com,http://blog.debugtalk.com --crawl-mode bfs --max-depth 10 --concurrency 20
```

Crawl with different cookies.

```text
$ python main.py --seeds http://debugtalk.com --crawl-mode BFS --max-depth 10 --concurrency 50 --cookies 'lang:en,country:us|lang:zh,country:cn'
```

## License

Open source licensed under the MIT license (see LICENSE file for details).

## Supported Python Versions

WebCrawler supports Python 2.7, 3.3, 3.4, 3.5, and 3.6.