# WebCrawler

A simple web crawler, mainly targets for link validation test.

## Features

- running in BFS or DFS mode
- specify concurrent running workers in BFS mode
- crawl seeds can be set to more than one urls
- configure hyper links regex, including match type and ignore type
- group visited urls by HTTP status code
- flexible configuration in YAML
- send test result by mail, through SMTP protocol or mailgun service

## Install

`WebCrawler` can be installed as a CLI tool, or just be used as a script. You can make your preference choice.

If you want to install `WebCrawler`, execute the following command, and all dependencies will be installed as well. Then you can use `webcrawler` CLI tool.

```bash
$ python setup.py install
$ webcrawler -h
```

If you prefer to use `WebCrawler` as a script, you should install dependencies first, then you can start `WebCrawler` through `python main.py` entrance.

```bash
$ pip install -r requirements.txt
$ python main.py -h
```

## Usage

```text
$ python main.py -h
# same as:
$ webcrawler -h
usage: webcrawler [-h] [--log-level LOG_LEVEL] [--seeds SEEDS]
                  [--crawl-mode CRAWL_MODE] [--max-depth MAX_DEPTH]
                  [--max-concurrent-workers MAX_CONCURRENT_WORKERS]
                  [--job-url JOB_URL] [--build-number BUILD_NUMBER]
                  [--smtp-host-port SMTP_HOST_PORT] [--mailgun-id MAILGUN_ID]
                  [--mailgun-key MAILGUN_KEY]
                  [--email-auth-username EMAIL_AUTH_USERNAME]
                  [--email-auth-password EMAIL_AUTH_PASSWORD]
                  [--email-recepients EMAIL_RECEPIENTS]

A web crawler for testing website links validation.

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        Specify logging level, default is INFO.
  --seeds SEEDS         Specify crawl seed url(s), several urls can be
                        specified with pipe; if auth needed, seeds can be
                        specified like user1:pwd1@url1|user2:pwd2@url2
  --crawl-mode CRAWL_MODE
                        Specify crawl mode, BFS or DFS.
  --max-depth MAX_DEPTH
                        Specify max crawl depth.
  --max-concurrent-workers MAX_CONCURRENT_WORKERS
                        Specify max concurrent workers number.
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
```

## Examples

Crawl in BFS mode with 20 concurrent workers, and set maximum depth to 5.

```bash
$ webcrawler --seeds http://debugtalk.com --crawl-mode bfs --max-depth 5 --max-concurrent-workers 20
```

Crawl in DFS mode, and set maximum depth to 10.

```bash
$ webcrawler --seeds http://debugtalk.com --crawl-mode dfs --max-depth 10
```

Crawl several websites in BFS mode with 20 concurrent workers, and set maximum depth to 10.

```bash
$ webcrawler --seeds http://debugtalk.com,http://blog.debugtalk.com --crawl-mode bfs --max-depth 10 --max-concurrent-workers 20
```

## License

Open source licensed under the MIT license (see LICENSE file for details).

## Supported Python Versions

WebCrawler supports Python 2.7, 3.3, 3.4, 3.5, and 3.6.