# -*- coding: utf-8 -*-
"""
Classes that handle sending reports for EnterpriseCustomers.
"""
from __future__ import absolute_import, unicode_literals

import csv
import datetime
import logging
import os
from smtplib import SMTPException
from uuid import UUID

from enterprise_reporting.clients.vertica import VerticaClient
from enterprise_reporting.utils import compress_and_encrypt, send_email_with_attachment, decrypt_string

LOGGER = logging.getLogger(__name__)


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
        'user_account_creation_date',
        'user_email',
        'user_username',
        'user_age',
        'user_level_of_education',
        'user_gender',
        'user_country_code',
        'country_name',
        'has_passed',
        'last_activity_date',
        'user_current_enrollment_mode',
    )
    REPORT_FILE_NAME_FORMAT = "{path}/{enterprise_id}_{date}.{extension}"
    REPORT_EMAIL_SUBJECT = 'edX Learner Report'
    REPORT_EMAIL_BODY = ''
    REPORT_EMAIL_FROM_EMAIL = os.environ.get('SEND_EMAIL_FROM')

    FILE_WRITE_DIRECTORY = '/tmp'

    def __init__(self, reporting_config):
        """
        Initialize with an EnterpriseCustomerReportingConfiguration.
        """
        self.reporting_config = reporting_config
        self.vertica_client = VerticaClient(
            os.environ.get('VERTICA_HOST'),
            os.environ.get('VERTICA_USERNAME'),
            os.environ.get('VERTICA_PASSWORD')
        )
        self.vertica_client.connect()

    def send_enterprise_report(self):
        """
        Query the data warehouse (vertica) and export data to a csv file.

        This file will get encrypted and emailed to the Enterprise Customer.
        """
        enterprise_customer_name = self.reporting_config['enterprise_customer']['name']

        LOGGER.info('Starting process to send email report to {}'.format(enterprise_customer_name))

        # initialize base csv file and file writer
        data_report_file_name, data_report_file_writer = self._create_data_report_csv_writer()

        # query vertica and write each row to the file
        LOGGER.debug('Querying Vertica for data for {}'.format(enterprise_customer_name))
        data_report_file_writer.writerows(self._query_vertica())

        # create a password encrypted zip file
        LOGGER.debug('Encrypting data report for {}'.format(enterprise_customer_name))
        data_report_zip_name = compress_and_encrypt(
            data_report_file_name,
            decrypt_string(self.reporting_config['password'], self.reporting_config['initialization_vector'])
        )

        # email the file to the email address in the configuration
        LOGGER.debug('Sending encrypted data to {}'.format(enterprise_customer_name))
        try:
            send_email_with_attachment(
                self.REPORT_EMAIL_SUBJECT,
                self.REPORT_EMAIL_BODY,
                self.REPORT_EMAIL_FROM_EMAIL,
                self.reporting_config['email'],
                data_report_zip_name
            )
        except SMTPException:
            LOGGER.exception('Failed to send email for {}'.format(enterprise_customer_name))

        self._cleanup()

    def _create_data_report_csv_writer(self):
        """
        Create a csv file and file writer with the field headers for the data report.
        """
        data_report_file_name = self.REPORT_FILE_NAME_FORMAT.format(
            path=self.FILE_WRITE_DIRECTORY,
            enterprise_id=self.reporting_config['enterprise_customer']['uuid'],
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
            extension='csv',
        )
        data_report_file = open(data_report_file_name, 'w')  # pylint: disable=open-builtin
        data_report_file_writer = csv.writer(data_report_file)
        data_report_file_writer.writerow(self.VERTICA_QUERY_FIELDS)
        return data_report_file_name, data_report_file_writer

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
