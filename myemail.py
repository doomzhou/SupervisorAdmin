#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import sys
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def mailsender(mailfrom, mailfrompass, smtpser, smtpport, mailto, mailcontent):
    msg = MIMEMultipart('alternative')
    msg['From'] = mailfrom
    msg['Subject'] = "用户验证"
    toaddr = mailto
    content = mailcontent
    msg.attach(MIMEText(content, 'plain'))
    s = smtplib.SMTP_SSL(smtpser, port=smtpport)
    s.login(msg['From'], mailfrompass)
    s.sendmail(msg['From'], toaddr,  msg.as_string())
    s.quit()


if __name__ == '__main__':
    pass
