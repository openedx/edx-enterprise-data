# -*- coding: utf-8 -*-
"""
Utility functions for Enterprise Reporting.
"""
from __future__ import absolute_import, unicode_literals

import datetime
import logging
import os
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import open  # pylint: disable=redefined-builtin

import boto3
import pyminizip
import pytz
from cryptography.fernet import Fernet
from fernet_fields.hkdf import derive_fernet_key

from django.utils.encoding import force_text

LOGGER = logging.getLogger(__name__)

COMPRESSION_LEVEL = 4

FREQUENCY_TYPE_DAILY = 'daily'
FREQUENCY_TYPE_MONTHLY = 'monthly'
FREQUENCY_TYPE_WEEKLY = 'weekly'

AWS_REGION = 'us-east-1'


def compress_and_encrypt(filename, password):
    """
    Given a file and a password, create an encrypted zip file. Return the new filename.
    """
    zip_filename = re.sub(r'\.(\w+)$', '.zip', filename)
    if filename == zip_filename:
        LOGGER.warn('Unable to determine filename for compressing {}, '
                    'file must have a valid extension that is not .zip'.format(filename))
        return None

    pyminizip.compress(filename, zip_filename, password, COMPRESSION_LEVEL)
    return zip_filename


def send_email_with_attachment(subject, body, from_email, to_email, filename):
    """
    Send an email with a file attachment.

    Adapted from https://gist.github.com/yosemitebandit/2883593
    """
    # connect to SES
    client = boto3.client('ses', region_name=AWS_REGION)

    # the message body
    msg_body = MIMEText(body)
    
    # the attachment
    msg_attachment = MIMEApplication(open(filename, 'rb').read())
    msg_attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
    msg_attachment.set_type('application/zip')

    # iterate over each email in the list to send emails independently
    for email in to_email:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = email

        # what a recipient sees if they don't use an email reader
        msg.preamble = 'Multipart message.\n'

        # attach the message body and attachment
        msg.attach(msg_body)
        msg.attach(msg_attachment)

        # and send the message
        result = client.send_raw_email(RawMessage={'Data': msg.as_string()}, Source=msg['From'], Destinations=[email])
        LOGGER.debug(result)


def is_current_time_in_schedule(frequency, hour_of_day, day_of_month=None, day_of_week=None):
    """
    Determine if the current time is in the range specified by this configuration's schedule.
    """
    est_timezone = pytz.timezone('US/Eastern')
    current_est_time = datetime.datetime.now(est_timezone)
    current_hour_of_day = current_est_time.hour
    current_day_of_week = current_est_time.weekday()
    current_day_of_month = current_est_time.day

    # All configurations have an hour of the day, so the hour must always match in order to send a report.
    if hour_of_day == current_hour_of_day:
        # If reports should be sent monthly and today is the same as the day configured, return True
        if frequency == FREQUENCY_TYPE_MONTHLY and day_of_month == current_day_of_month:
            return True
        # If reports should be sent weekly and today is the same as the day configured, return True
        elif frequency == FREQUENCY_TYPE_WEEKLY and day_of_week == current_day_of_week:
            return True
        # If reports should be sent daily, return True
        elif frequency == FREQUENCY_TYPE_DAILY:
            return True

    return False


def decrypt_string(string):
    """
    Decrypts a string that was encrypted using Fernet symmetric encryption.
    """
    fernet = Fernet(
        derive_fernet_key(
            os.environ.get('LMS_FERNET_KEY')
        )
    )
    return force_text(fernet.decrypt(bytes(string, 'utf-8')))
