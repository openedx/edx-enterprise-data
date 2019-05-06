# -*- coding: utf-8 -*-
"""
Utility functions for Enterprise Reporting.
"""
from __future__ import absolute_import, unicode_literals

import datetime
import logging
import os
import re
from collections import OrderedDict
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import open  # pylint: disable=redefined-builtin

import boto3
import pgpy
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


def compress_and_encrypt(files, password=None, pgp_key=''):
    """
    Given file(s) and a password or a PGP key,
    create a password protected or encrypted compressed file.
    Return the new filename.
    """
    if pgp_key:
        zipfile = _get_compressed_file(files)
        return _get_encrypted_file(zipfile, pgp_key)
    else:
        return _get_compressed_file(files, password)


def _get_encrypted_file(zipfile, pgp_key):
    """
    Given a file and a pgp public key, create an encrypted file. Return the new filename.
    """
    rsa_pub, _ = pgpy.PGPKey.from_blob(pgp_key)
    message = pgpy.PGPMessage.new(zipfile, file=True)
    pgpfile = '{}.pgp'.format(zipfile)
    encrypted_message = rsa_pub.encrypt(message)
    with open(pgpfile, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_message.__bytes__())
    return pgpfile


def _get_compressed_file(files, password=None):
    """
    Given file(s) and a password, create a zip file. Return the new filename.
    """
    multiple_files = len(files) > 1
    # Replace the data and report type with just `.zip`.
    zipfile = re.sub(r'(_(\w+))?\.(\w+)$', '.zip', files[0].name)
    compression = pyminizip.compress_multiple if multiple_files else pyminizip.compress
    src_file_path_prefix = [] if multiple_files else None
    compression(
        [f.name for f in files] if multiple_files else files[0].name,
        src_file_path_prefix,
        zipfile,
        password,
        COMPRESSION_LEVEL
    )
    return zipfile


def prepare_attachments(attachment_data):
    """
    Helper function to create a list contain file attachment objects
    for use with MIMEMultipart

    attachment_data should be a dictionary, with filenames as keys, and None
        or a string as value. If the value is None, the key is assumed to be a
        filename

    attachment_data = {
        'my_file_name.csv': '1,1,1,1,1,\n2,2,2,2,2\n3,3,3,3,3\n'
        '/abs/path/to/myfile.csv': None
    }

    Returns a list of MIMEApplication objects
    """

    attachments = []
    for filename, data in attachment_data.items():
        if data is None:
            msg_attachment = MIMEApplication(open(filename, 'rb').read())
        else:
            msg_attachment = MIMEApplication(data)
        msg_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=os.path.basename(filename)
        )
        msg_attachment.set_type('application/zip')
        attachments.append(msg_attachment)

    return attachments


def send_email_with_attachment(subject, body, from_email, to_email, attachment_data):
    """
    Send an email with a file attachment.

    Adapted from https://gist.github.com/yosemitebandit/2883593

    attachment_data should be a dict of file name and data key-value pairs
    """
    # connect to SES
    client = boto3.client('ses', region_name=AWS_REGION)

    # the message body
    msg_body = MIMEText(body)

    # the attachment
    attachments = prepare_attachments(attachment_data)

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
        for msg_attachment in attachments:
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


def flatten_dict(d, target='key' or 'value'):
    """
    Flattens a dict object into a list.

    The behavior is as such for targeting keys:
        * Each key is concatenated into the list.
        * Each key with a list value has the list's indices formatted (see [1]) and concatenated into the list.
        * Each key with a dict value has the dict's sub-keys formatted (see [1]) and concatenated into the list.
        * Sub-objects are recursively flattened.

    The behavior is as such for targeting values:
        * Each non-list value is concatenated into the list.
        * Each list value has its entries concatenated into the list.
        * Sub-objects are recursively flattened.

    WARNING: Appropriately flattening lists with a mixture of dict and non-dict objects within them is unsupported.

    [1]: The nested-value formatting function can be found nested within this function. (No pun intended).

    # TODO: This beastly mess of a house of cards *needs* a refactor at some point. Make do with comments for now.
    # TODO: This can probably be separated into a dedicated Python library somewhere sometime in the future.
    """
    def format_nested(nested, _key=None):
        if _key is None:
            _key = key
        return '{}_{}'.format(_key, nested)

    flattened = []
    target_is_key = target == 'key'
    for key, value in OrderedDict(sorted(d.items())).items():

        # Simple case: recursively flatten the dictionary.
        if isinstance(value, dict):
            flattened += map(
                format_nested if target_is_key else lambda x: x,
                flatten_dict(value, target=target)
            )

        # We are suddenly in muddy waters, because lists can have multiple types within them in JSON.
        elif isinstance(value, list):
            items_are_dict = [isinstance(item, dict) for item in value]
            items_are_list = [isinstance(item, list) for item in value]

            # To help reduce the complexity here, let's not support this case.
            # Besides, most sensible APIs won't bump into this case.
            if any(items_are_dict) and not all(items_are_dict):
                raise NotImplementedError("Ability to flatten dict with list of mixed dict and non-dict types "
                                          "is not currently supported")

            # Same here, this is just weird.
            if any(items_are_list):
                raise NotImplementedError("Ability to flatten a dict with lists within lists "
                                          "is not currently supported. And we'd like to ask you to take it easy.")

            # This case is common, but a little complex.
            elif all(items_are_dict):
                for index, item in enumerate(value):
                    _flattened_dict = flatten_dict(item, target=target)

                    # In this case we actually want to prepend the dict's index in the list to each flattened dict.
                    if target_is_key:
                        _flattened_dict = [format_nested(flattened_item, _key=index)
                                           for flattened_item in _flattened_dict]

                    flattened += map(format_nested if target_is_key else lambda x: x, _flattened_dict)

            # All items are non-dict, so just directly add either the index or the value.
            else:
                flattened += map(format_nested, range(len(value))) if target_is_key else value

        # Kindergarten -- just add to the list.
        else:
            flattened.append(key if target_is_key else value)
    return flattened


def generate_data(item, target='key' or 'value'):
    """
    Either return a list of JSON data objects or
    List of headers depends upon the target.
    """
    data = []
    target_is_key = target == 'key'
    for key, value in OrderedDict(sorted(item.items())).items():
        if target_is_key:
            data.append(key)
            continue

        # For empty list we are just writing an empty string ''.
        if isinstance(value, list) and not len(value):
            value = ''

        data.append(value)

    return data
