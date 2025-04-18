"""
Classes that handle sending reports for enterprise customers with specific delivery methods.
"""

import logging
import os
from smtplib import SMTPException

import paramiko

from enterprise_reporting.constants import SFTP_OPS_GENIE_EMAIL_ALERT_EMAILS, SFTP_OPS_GENIE_EMAIL_ALERT_FROM_EMAIL
from enterprise_reporting.utils import (
    compress_and_encrypt,
    decrypt_string,
    retry_on_exception,
    send_email_with_attachment,
)

LOGGER = logging.getLogger(__name__)


class DeliveryMethod:
    """
    Base class for different types of Enterprise report delivery methods.
    """

    def __init__(self, reporting_config, password):
        """Initialize the SFTP Delivery Method."""
        self.enterprise_customer_name = reporting_config['enterprise_customer']['name']
        self.data_type = reporting_config['data_type']
        self.report_type = reporting_config['report_type']
        self.password = password
        self.encrypted_password = reporting_config['encrypted_password']
        self.pgp_encryption_key = reporting_config.get('pgp_encryption_key')
        self.enable_compression = reporting_config.get('enable_compression')

    def send(self, files):
        """Base method for sending files, to perform common sending logic."""
        if self.enable_compression:
            LOGGER.info(f'Encrypting data report for {self.enterprise_customer_name}')
            zip_password = decrypt_string(
                self.encrypted_password) if self.encrypted_password else self.encrypted_password
            zip_file = compress_and_encrypt(files, zip_password, self.pgp_encryption_key)
            return [zip_file]
        return [file.name for file in files]


class SMTPDeliveryMethod(DeliveryMethod):
    """
    Class that handles sending an enterprise report file via email.
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
        """Send the given files through SMTP."""
        attachment_data = {file: None for file in super().send(files)}
        LOGGER.info(f'Emailing encrypted data to {self.enterprise_customer_name}')
        try:
            send_email_with_attachment(
                self.REPORT_EMAIL_SUBJECT.format(enterprise_name=self.enterprise_customer_name),
                self.REPORT_EMAIL_BODY.format(type=self.data_type),
                self.REPORT_EMAIL_FROM_EMAIL,
                self.email,
                attachment_data
            )
        except SMTPException:
            LOGGER.exception('Failed to send email report to {} for {}'.format(
                self.email,
                self.enterprise_customer_name
            ))
        else:
            LOGGER.info('Email report successfully sent to {} for {}'.format(
                self.email,
                self.enterprise_customer_name
            ))


class SFTPDeliveryMethod(DeliveryMethod):
    """
    Class that handles sending an enterprise report file via SFTP.
    """
    sender_email = SFTP_OPS_GENIE_EMAIL_ALERT_FROM_EMAIL
    receiver_emails = SFTP_OPS_GENIE_EMAIL_ALERT_EMAILS

    def __init__(self, reporting_config, password):
        """Initialize the SFTP Delivery Method."""
        super().__init__(reporting_config, password)
        self.hostname = reporting_config['sftp_hostname']
        self.port = reporting_config['sftp_port']
        self.username = reporting_config['sftp_username']
        self.file_path = reporting_config['sftp_file_path']

    @retry_on_exception(max_retries=3, delay=2, backoff=2)
    def send_over_sftp(self, data_reports):
        """
        Send the reports via SFTP, retry on exception.
        """
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
        for report in data_reports:
            sftp.put(
                report,
                os.path.join(self.file_path, os.path.basename(report))
            )
        sftp.close()
        ssh.close()

    def send(self, files):
        """Send the given files through SFTP."""
        try:
            data_reports = super().send(files)
            self.send_over_sftp(data_reports)
        except Exception:  # pylint: disable=broad-except
            email_subject = f'SFTP transmission failed for {self.enterprise_customer_name}'
            email_body = f'Failed to send {self.data_type} report for {self.enterprise_customer_name}'
            LOGGER.exception(f'SFTP transmission failed for {self.enterprise_customer_name}')
        else:
            LOGGER.info(f'Successfully sent report via sftp for {self.enterprise_customer_name}')
            email_subject = f'SFTP transmission successful for {self.enterprise_customer_name}'
            email_body = f'SFTP transmission successful for {self.enterprise_customer_name}'

        send_email_with_attachment(
            subject=email_subject,
            body=email_body,
            from_email=self.sender_email,
            to_email=self.receiver_emails,
            attachment_data={},
        )
