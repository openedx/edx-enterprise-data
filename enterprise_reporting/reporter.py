# -*- coding: utf-8 -*-
"""
Classes that handle sending reports for EnterpriseCustomers.
"""
from __future__ import absolute_import, unicode_literals

import csv
import datetime
import logging
import os
from io import open  # pylint: disable=redefined-builtin
from smtplib import SMTPException
from uuid import UUID

import paramiko
from enterprise_reporting.clients.vertica import VerticaClient
from enterprise_reporting.utils import compress_and_encrypt, decrypt_string, send_email_with_attachment

LOGGER = logging.getLogger(__name__)


class EnterpriseReportSenderFactory(object):
    """
    Factory that creates the EnterpriseReportSender given a reporting configuration.
    """

    @staticmethod
    def create(reporting_config):
        """
        Create the EnterpriseReportSender and all of its dependencies.
        """
        enterprise_customer_name = reporting_config['enterprise_customer']['name']
        vertica_client = VerticaClient(
            os.environ.get('VERTICA_HOST'),
            os.environ.get('VERTICA_USERNAME'),
            os.environ.get('VERTICA_PASSWORD')
        )
        if reporting_config['delivery_method'] == 'email':
            LOGGER.debug('{} is configured to send the report via email to {}'.format(
                enterprise_customer_name,
                reporting_config['email'],
            ))
            delivery_method = EmailDeliveryMethod(
                reporting_config['email'],
                decrypt_string(reporting_config['encrypted_password']),
                enterprise_customer_name
            )
        elif reporting_config['delivery_method'] == 'sftp':
            LOGGER.debug('{} is configured to send the report via sftp'.format(enterprise_customer_name))
            delivery_method = SFTPDeliveryMethod(
                reporting_config['sftp_hostname'],
                reporting_config['sftp_port'],
                reporting_config['sftp_username'],
                decrypt_string(reporting_config['encrypted_sftp_password']),
                reporting_config['sftp_file_path'],
                enterprise_customer_name
            )
        else:
            raise Exception

        return EnterpriseReportSender(reporting_config, vertica_client, delivery_method)


class EnterpriseReportSender(object):
    """
    Class that handles the process of sending a data report to an Enterprise Customer.
    """

    VERTICA_QUERY = ("SELECT {fields} FROM business_intelligence.enterprise_enrollment"
                     " WHERE enterprise_id = '{enterprise_id}' AND consent_granted = 1")
    VERTICA_QUERY_FIELDS = (
        'enterprise_user_id',
        'lms_user_id',
        'enterprise_sso_uid',
        'enrollment_created_timestamp',
        'consent_granted',
        'course_id',
        'course_title',
        'course_duration',
        'course_min_effort',
        'course_max_effort',
        'user_account_creation_date',
        'user_email',
        'user_username',
        'user_age',
        'user_level_of_education',
        'user_gender',
        'user_country_code',
        'country_name',
        'has_passed',
        'passed_timestamp',
        'time_spent_hours',
        'last_activity_date',
        'user_current_enrollment_mode',
    )
    REPORT_FILE_NAME_FORMAT = "{path}/{enterprise_id}_{date}.{extension}"
    FILE_WRITE_DIRECTORY = '/tmp'

    def __init__(self, reporting_config, vertica_client, delivery_method):
        """
        Initialize with an EnterpriseCustomerReportingConfiguration.
        """
        self.reporting_config = reporting_config
        self.vertica_client = vertica_client
        self.delivery_method = delivery_method

    def send_enterprise_report(self):
        """
        Query the data warehouse (vertica) and export data to a csv file.

        This file will get encrypted and emailed to the Enterprise Customer.
        """
        enterprise_customer_name = self.reporting_config['enterprise_customer']['name']

        LOGGER.info('Starting process to send report to {}'.format(enterprise_customer_name))

        # Query vertica and write output to csv file.
        self.vertica_client.connect()
        data_report_file_name = self.REPORT_FILE_NAME_FORMAT.format(
            path=self.FILE_WRITE_DIRECTORY,
            enterprise_id=self.reporting_config['enterprise_customer']['uuid'],
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
            extension='csv',
        )
        with open(data_report_file_name, 'w') as data_report_file:
            data_report_file_writer = csv.writer(data_report_file)
            data_report_file_writer.writerow(self.VERTICA_QUERY_FIELDS)
            LOGGER.debug('Querying Vertica for data for {}'.format(enterprise_customer_name))
            data_report_file_writer.writerows(self._query_vertica())

        # Send the data based on the delivery method.
        self.delivery_method.send(data_report_file_name)

        self._cleanup()

    def _query_vertica(self):
        """
        Use a connection to Vertica to execute the report query.
        """
        query = self.VERTICA_QUERY.format(
            fields=','.join(self.VERTICA_QUERY_FIELDS),
            enterprise_id=UUID(self.reporting_config['enterprise_customer']['uuid']).hex
        )
        LOGGER.debug('Executing Vertica query: {}'.format(query))
        return self.vertica_client.stream_results(query)

    def _cleanup(self):
        """
        Perform various cleanup operations after we've attempted (successfully or not) to send a report.
        """
        self.vertica_client.close_connection()


class EmailDeliveryMethod(object):
    """
    Class that handles sending an enterprise report file via email as an encrypted zip file.
    """

    REPORT_EMAIL_SUBJECT = '{enterprise_name} edX Learner Data'
    REPORT_EMAIL_BODY = """
    Please find attached employee progress data for courses on edX.
    For any questions or concerns, please contact your edX sales representative.
    Thanks,
    The edX for Business Team
    """
    REPORT_EMAIL_FROM_EMAIL = os.environ.get('SEND_EMAIL_FROM')

    def __init__(self, email, password, enteprise_customer_name):
        """
        Initialize the Email Delivery Method.
        """
        self.email = email if isinstance(email, list) else [email] # convert to list if it's not already
        self.password = password
        self.enterprise_customer_name = enteprise_customer_name

    def send(self, enterprise_report_file_name):
        """
        Send the given file with the configured information.
        """
        # create a password encrypted zip file
        LOGGER.info('Encrypting data report for {}'.format(self.enterprise_customer_name))
        data_report_zip_name = compress_and_encrypt(enterprise_report_file_name, self.password)

        data_report_subject = self.REPORT_EMAIL_SUBJECT.format(
            enterprise_name=self.enterprise_customer_name
        )

        # email the file to the email address(es) in the configuration
        LOGGER.info('Sending encrypted data to {}'.format(self.enterprise_customer_name))
        try:
            send_email_with_attachment(
                data_report_subject,
                self.REPORT_EMAIL_BODY,
                self.REPORT_EMAIL_FROM_EMAIL,
                self.email,
                data_report_zip_name
            )
            LOGGER.info('Email report with encrypted zip successfully sent to {} for {}'.format(
                ', '.join(self.email),
                self.enterprise_customer_name
            ))
        except SMTPException:
            LOGGER.exception('Failed to send email report to {} for {}'.format(
                self.email,
                self.enterprise_customer_name
            ))


class SFTPDeliveryMethod(object):
    """
    Class that handles sending an enterprise report file via SFTP.
    """

    def __init__(self, hostname, port, username, password, file_path, enterprise_customer_name):
        """
        Initialize the SFTP Delivery Method.
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.file_path = file_path
        self.enterprise_customer_name = enterprise_customer_name

    def send(self, enterprise_report_file_name):
        """
        Send the given file with the configured information.
        """
        LOGGER.info('Connecting via sftp to remote host {} for {}'.format(
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
            enterprise_report_file_name,
            os.path.join(self.file_path, os.path.basename(enterprise_report_file_name))
        )
        sftp.close()
        ssh.close()
        LOGGER.info('Successfully sent report via sftp for {}'.format(self.enterprise_customer_name))
