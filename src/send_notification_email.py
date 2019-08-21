# send_notification_email.py
""" This routine sends and email alerting the user of missing fields. """

import boto3
from botocore.errorfactory import ClientError
from sentry_sdk import capture_exception
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def create_and_send_email_notification(missing_fields, notification_email_address, sender):
    """ Create and then send an email alerting someone about missing fields """
    recipients = notification_email_address.split(",")
    subject = "Metadata is missing required fields"
    body_html = _create_email_html_body(missing_fields)
    body_text = ''
    _send_email(sender, recipients, subject, body_html, body_text)


def _create_email_html_body(missing_fields):
    """ Create the body of the email in html format """
    # self.config['notification-email-address']
    body_html = """<html>
    <head></head>
    <body>
    <h1>Missing required fields when processing metadata</h1>
    <p> """ + missing_fields + """</p>
    </body>
    </html>"""
    body_html = body_html.replace('\n', '<br/>')
    return body_html


def _send_email(sender, recipients, subject, body_html, body_text):
    AWS_REGION = "us-east-1"
    CHARSET = "UTF-8"
    client = boto3.client('ses', region_name=AWS_REGION)
    email_message_json = {
        'Body': {},
        'Subject': {
            'Charset': CHARSET,
            'Data': subject,
        },
    }
    if body_html > '':
        email_message_json['Body']['Html'] = {'Charset': CHARSET, 'Data': body_html}
    elif body_text > '':
        email_message_json['Body']['Text'] = {'Charset': CHARSET, 'Data': body_text}
    try:
        response = client.send_email(
            Destination={'ToAddresses': recipients},
            Message=email_message_json,
            Source=sender
        )
    except ClientError as e:
        capture_exception(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    return
