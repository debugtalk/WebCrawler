import sys
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import requests
from .helpers import color_logging

class MailSender(object):

    def __init__(self, config):
        """
        config = {
            'host': 'mail.debugtalk.com',
            'port': 25,
            'username': 'mail@debugtalk.com',
            'password': 'xxxxxx',
            'debug': False
        }
        """
        self.host_port = "{}:{}".format(config['host'], config['port'])
        self.username = config['username']
        self.password = config['password']

        if config['port'] == 25:
            self.sender = smtplib.SMTP()
        elif config['port'] in [587, 465]:
            self.sender = smtplib.SMTP_SSL()

        debug = config.get('debug', False)
        self.sender.set_debuglevel(debug)

    def __enter__(self):
        self.sender.connect(self.host_port)
        self.sender.ehlo_or_helo_if_needed()
        self.sender.login(self.username, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sender.quit()
        return True

    def send_mail(self, subject, recipients, mail_content):

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        msg = MIMEText(mail_content['content'], mail_content['type'], 'utf-8')
        msg['From'] = _format_addr('DebugTalk <%s>' % self.username)
        msg['To'] = ','.join(recipients)
        msg['Subject'] = Header(subject, 'utf-8').encode()

        self.sender.sendmail(self.username, recipients, msg.as_string())


class Mailgun(object):

    def __init__(self, config):
        """
        config = {
            'api-id': 'samples.mailgun.org',
            'api-key': 'key-3ax6xnjp29jd6fds4gc373sgvjxteol0',
            'sender': 'excited@samples.mailgun.org'
        }
        """
        self.api_url = "https://api.mailgun.net/v3/{}/messages".format(config['api-id'])
        self.api_key = config['api-key']
        self.sender = config['sender']

    def send_mail(self, subject, recipients, mail_content):
        data={
            "from": "postmaster <{}>".format(self.sender),
            "to": recipients,
            "subject": subject
        }
        data[mail_content['type']] = mail_content['content']
        resp = requests.post(
            self.api_url,
            auth=("api", self.api_key),
            data=data
        )
        try:
            assert "Queued. Thank you." in resp.json()['message']
            color_logging(resp.text)
        except:
            color_logging(resp.text, 'ERROR')


def send_mail(args, mail_content):
    email_auth_username = args.email_auth_username
    email_recepients = args.email_recepients
    smtp_host_port = args.smtp_host_port
    email_auth_password = args.email_auth_password
    mailgun_id = args.mailgun_id
    mailgun_key = args.mailgun_key
    if not email_auth_username or not email_recepients:
        color_logging("Mail will not be sent. Run `python main.py crawler -h` for help.", 'WARNING')
        sys.exit(0)

    subject = 'web links test result'
    email_recepients = email_recepients.split(',')

    if smtp_host_port and email_auth_password:
        color_logging("Send mail with SMTP account.")
        smtp_host, smtp_port = smtp_host_port.split(':')
        mail_config = {
            'host': smtp_host,
            'port': int(smtp_port),
            'username': email_auth_username,
            'password': email_auth_password
        }
        with MailSender(mail_config) as mail_sender:
            mail_sender.send_mail(subject, email_recepients, mail_content)
    elif mailgun_id and mailgun_key:
        color_logging("Send mail with mailgun account.")
        config = {
            'api-id': mailgun_id,
            'api-key': mailgun_key,
            'sender': email_auth_username
        }
        Mailgun(config).send_mail(subject, email_recepients, mail_content)
