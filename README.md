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
$ pip install -U git+https://github.com/debugtalk/WebCrawler.git#egg=WebCrawler --process-dependency-links
```

To ensure the installation or upgrade is successful, you can execute command `webcrawler -V` to see if you can get the correct version number.

```bash
$ webcrawler -V
jenkins-mail-py version: 0.2.4
WebCrawler version: 0.3.0
```

## Usage

```text
$ webcrawler -h
usage: webcrawler [-h] [-V] [--log-level LOG_LEVEL]
                  [--config-file CONFIG_FILE] [--seeds SEEDS]
                  [--include-hosts INCLUDE_HOSTS] [--cookies COOKIES]
                  [--crawl-mode CRAWL_MODE] [--max-depth MAX_DEPTH]
                  [--concurrency CONCURRENCY] [--save-results SAVE_RESULTS]
                  [--grey-user-agent GREY_USER_AGENT]
                  [--grey-traceid GREY_TRACEID]
                  [--grey-view-grey GREY_VIEW_GREY]
                  [--mailgun-api-id MAILGUN_API_ID]
                  [--mailgun-api-key MAILGUN_API_KEY]
                  [--mail-sender MAIL_SENDER]
                  [--mail-recepients [MAIL_RECEPIENTS [MAIL_RECEPIENTS ...]]]
                  [--mail-subject MAIL_SUBJECT] [--mail-content MAIL_CONTENT]
                  [--jenkins-job-name JENKINS_JOB_NAME]
                  [--jenkins-job-url JENKINS_JOB_URL]
                  [--jenkins-build-number JENKINS_BUILD_NUMBER]

A web crawler for testing website links validation.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show version
  --log-level LOG_LEVEL
                        Specify logging level, default is INFO.
  --config-file CONFIG_FILE
                        Specify config file path.
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
  --save-results SAVE_RESULTS
                        Specify if save results, default is NO.
  --grey-user-agent GREY_USER_AGENT
                        Specify grey environment header User-Agent.
  --grey-traceid GREY_TRACEID
                        Specify grey environment cookie traceid.
  --grey-view-grey GREY_VIEW_GREY
                        Specify grey environment cookie view_gray.
  --mailgun-api-id MAILGUN_API_ID
                        Specify mailgun api id.
  --mailgun-api-key MAILGUN_API_KEY
                        Specify mailgun api key.
  --mail-sender MAIL_SENDER
                        Specify email sender.
  --mail-recepients [MAIL_RECEPIENTS [MAIL_RECEPIENTS ...]]
                        Specify email recepients.
  --mail-subject MAIL_SUBJECT
                        Specify email subject.
  --mail-content MAIL_CONTENT
                        Specify email content.
  --jenkins-job-name JENKINS_JOB_NAME
                        Specify jenkins job name.
  --jenkins-job-url JENKINS_JOB_URL
                        Specify jenkins job url.
  --jenkins-build-number JENKINS_BUILD_NUMBER
                        Specify jenkins build number.
```

## Examples

Specify config file.

```bash
$ webcrawler --seeds http://debugtalk.com --crawl-mode bfs --max-depth 5 --config-file path/to/config.yml
```

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
$ webcrawler --seeds http://debugtalk.com --crawl-mode BFS --max-depth 10 --concurrency 50 --cookies 'lang:en,country:us|lang:zh,country:cn'
```

## Supported Python Versions

WebCrawler supports Python 2.7, 3.3, 3.4, 3.5, and 3.6.

## License

Open source licensed under the MIT license (see LICENSE file for details).
