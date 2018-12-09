# -*- coding: utf-8 -*-
"""
Classes that handle sending reports for enterprise customers with specific delivery methods.
"""

from __future__ import absolute_import, unicode_literals

import logging
import os
from smtplib import SMTPException

import paramiko

from enterprise_reporting.utils import compress_and_encrypt, send_email_with_attachment

LOGGER = logging.getLogger(__name__)


class DeliveryMethod(object):
    """
    Base class for different types of Enterprise report delivery methods.
    """

    def __init__(self, reporting_config, password):
        """Initialize the SFTP Delivery Method."""
        self.enterprise_customer_name = reporting_config['enterprise_customer']['name']
        self.data_type = reporting_config['data_type']
        self.report_type = reporting_config['report_type']
        self.password = password

    def send(self, files):
        """Base method for sending files, to perform common sending logic."""
        LOGGER.info('Encrypting data report for {}'.format(self.enterprise_customer_name))
        return compress_and_encrypt(files, self.password)


class SMTPDeliveryMethod(DeliveryMethod):
    """
    Class that handles sending an enterprise report file via email as an encrypted zip file.
    """

    REPORT_EMAIL_FROM_EMAIL = os.environ.get('SEND_EMAIL_FROM')
    REPORT_EMAIL_SUBJECT = '{enterprise_name} edX Learner Data'
    REPORT_EMAIL_BODY = """
    Please find the attached {type} data for courses on edX.
    For any questions or concerns, please contact your edX sales representative.
    Thanks,
    The edX for Business Team
    """

    def __init__(self, reporting_config, password):
        """Initialize the SMTP Delivery Method."""
        super().__init__(reporting_config, password)
        self._email = reporting_config['email']

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        """Make the internal email value a list if there are multiple emails."""
        self._email = value if isinstance(value, list) else [value]

    def send(self, files):
        """Send the given files in zip format through SMTP."""
        data_report_zipped = super().send(files)
        LOGGER.info('Emailing encrypted data as a ZIP to {}'.format(self.enterprise_customer_name))
        try:
            send_email_with_attachment(
                self.REPORT_EMAIL_SUBJECT.format(enterprise_name=self.enterprise_customer_name),
                self.REPORT_EMAIL_BODY.format(type=self.data_type),
                self.REPORT_EMAIL_FROM_EMAIL,
                self.email,
                data_report_zipped
            )
        except SMTPException:
            LOGGER.exception('Failed to send email report to {} for {}'.format(
                self.email,
                self.enterprise_customer_name
            ))
        else:
            LOGGER.info('Email report with encrypted zip successfully sent to {} for {}'.format(
                self.email,
                self.enterprise_customer_name
            ))


class SFTPDeliveryMethod(DeliveryMethod):
    """
    Class that handles sending an enterprise report file via SFTP.
    """

    def __init__(self, reporting_config, password):
        """Initialize the SFTP Delivery Method."""
        super().__init__(reporting_config, password)
        self.hostname = reporting_config['sftp_hostname']
        self.port = reporting_config['sftp_port']
        self.username = reporting_config['sftp_username']
        self.file_path = reporting_config['sftp_file_path']

    def send(self, files):
        """Send the given files in zip format through SFTP."""
        data_report_zipped = super().send(files)
        LOGGER.info('Connecting via SFTP to remote host {} for {}'.format(
            self.hostname,
            self.enterprise_customer_name
        ))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        sftp = ssh.open_sftp()
        sftp.put(
            data_report_zipped,
            os.path.join(self.file_path, os.path.basename(data_report_zipped))
        )
        sftp.close()
        ssh.close()
        LOGGER.info('Successfully sent report via sftp for {}'.format(self.enterprise_customer_name))
