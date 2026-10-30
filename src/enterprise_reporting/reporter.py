"""
Classes that handle sending reports for EnterpriseCustomers.
"""

import csv
import datetime
import json
import logging
import os
from collections import OrderedDict
from uuid import UUID

from enterprise_reporting.clients.enterprise import (
    AnalyticsDataApiClient,
    EnterpriseAPIClient,
    EnterpriseCatalogAPIClient,
    EnterpriseDataApiClient,
    EnterpriseDataV1ApiClient,
)
from enterprise_reporting.clients.s3 import S3Client
from enterprise_reporting.clients.vertica import VerticaClient
from enterprise_reporting.delivery_method import SFTPDeliveryMethod, SMTPDeliveryMethod
from enterprise_reporting.utils import (
    decrypt_string,
    extract_catalog_uuids_from_reporting_config,
    generate_data,
    retry_on_exception,
)

LOGGER = logging.getLogger(__name__)
NOW = datetime.datetime.now().strftime("%Y-%m-%d")


class EnterpriseReportSender:
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

    FILE_WRITE_DIRECTORY = '/tmp'

    def __init__(self, reporting_config, delivery_method):
        """Initialize with an EnterpriseCustomerReportingConfiguration."""
        self.reporting_config = reporting_config
        self.delivery_method = delivery_method
        self.enterprise_customer_uuid = reporting_config['enterprise_customer']['uuid']
        self.enterprise_customer_name = reporting_config['enterprise_customer']['name']
        self.data_type = reporting_config['data_type']
        self.report_type = reporting_config['report_type']

    @staticmethod
    def create(reporting_config):
        """Create the EnterpriseReportSender and all of its dependencies."""
        enterprise_customer_name = reporting_config['enterprise_customer']['name']
        delivery_method_str = reporting_config['delivery_method']
        if delivery_method_str == 'email':
            LOGGER.debug('{} is configured to send the report via SMTP to {}'.format(
                enterprise_customer_name,
                reporting_config['email'],
            ))
            decrypted_password = None
            if reporting_config['encrypted_password']:
                decrypted_password = decrypt_string(reporting_config['encrypted_password'])
            delivery_method = SMTPDeliveryMethod(reporting_config, decrypted_password)
        elif delivery_method_str == 'sftp':
            LOGGER.debug('{} is configured to send the report via SFTP to {}'.format(
                enterprise_customer_name,
                reporting_config['sftp_hostname'],
            ))
            delivery_method = SFTPDeliveryMethod(
                reporting_config,
                decrypt_string(reporting_config['encrypted_sftp_password']),
            )
        else:
            raise ValueError(f'Invalid delivery method: {delivery_method_str}')

        return EnterpriseReportSender(reporting_config, delivery_method)

    @property
    def data_report_file_name(self):
        """Get the full path to the report file."""
        date_str = f"_{NOW}" if self.reporting_config.get('include_date') else ""
        return "{dir}/{enterprise_id}_{data}_{ext}{date_str}.{ext}".format(
            dir=self.FILE_WRITE_DIRECTORY,
            enterprise_id=self.enterprise_customer_uuid,
            data=self.data_type,
            date_str=date_str,
            ext=self.report_type,
        )

    @property
    def data_report_file_name_with(self):
        """Get a full path to the report file that can be modified with arbitrary formatting."""
        return '_{}.'.join(self.data_report_file_name.rsplit('.'))

    @retry_on_exception(max_retries=2, delay=1, backoff=2)
    def send_enterprise_report(self):
        """Generate the report file of the appropriate type and send it through the configured delivery method."""
        LOGGER.info(f'Starting process to send report to {self.enterprise_customer_name}')
        files = self._generate_enterprise_report()
        if files:
            self.delivery_method.send(files)
        else:
            LOGGER.warning('No {} {} reports were generated for {}! Moving on...'.format(
                self.data_type,
                self.report_type,
                self.enterprise_customer_name
            ))

    def _generate_enterprise_report(self):
        """Calls the appropriate method for generating the report, e.g. the method for a CSV report of Catalog data."""
        LOGGER.info(f'Generating {self.data_type} report in {self.report_type} format...')
        return getattr(self, '_generate_enterprise_report_{type}_{ext}'.format(
            type=self.data_type,
            ext=self.report_type
        ))()

    def _generate_enterprise_report_progress_csv(self):
        """Query vertica and write output to csv file."""
        vertica_client = VerticaClient()
        vertica_client.connect()
        with open(self.data_report_file_name, 'w') as data_report_file:
            data_report_file_writer = csv.writer(data_report_file)
            data_report_file_writer.writerow(self.VERTICA_QUERY_FIELDS)
            query = self.VERTICA_QUERY.format(
                fields=','.join(self.VERTICA_QUERY_FIELDS),
                enterprise_id=UUID(self.enterprise_customer_uuid).hex
            )
            LOGGER.debug(f'Executing this Vertica query: {query}')
            data_report_file_writer.writerows(vertica_client.stream_results(query))
        vertica_client.close_connection()
        return [data_report_file]

    def get_s3_csv_path(self):
        """Return S3 CSV path for a manual report else raise an exception if path doesn't exist"""
        # <data_type>-<enterprise uuid>
        env_variable_name = f"{self.data_type}-{self.enterprise_customer_uuid.replace('-', '')}"
        s3_csv_path = os.environ.get(env_variable_name)

        if not s3_csv_path:
            raise ValueError(f'Invalid S3 CSV path. Path: [{s3_csv_path}]')

        LOGGER.info(
            'Enterprise UUID: [%s], Enterprise Name: [%s], Data Type: [%s], S3 CSV Path: [%s]',
            self.enterprise_customer_uuid,
            self.enterprise_customer_name,
            self.data_type,
            s3_csv_path,
        )

        return s3_csv_path

    def _generate_enterprise_report_grade_csv(self):
        """Query S3 and write output to csv file."""
        s3_client = S3Client()
        with open(self.data_report_file_name, 'wb') as data_report_file:
            LOGGER.debug('Fetching enterprise grade report from S3')
            s3_client.get_enterprise_report(self.get_s3_csv_path(), data_report_file)
        return [data_report_file]

    def _generate_enterprise_report_course_structure_csv(self):
        """Query S3 and write output to csv file."""
        s3_client = S3Client()
        with open(self.data_report_file_name, 'wb') as data_report_file:
            LOGGER.debug('Fetching enterprise course structure report from S3')
            s3_client.get_enterprise_report(self.get_s3_csv_path(), data_report_file)
        return [data_report_file]

    def _generate_enterprise_report_completion_csv(self):
        """Query S3 and write output to csv file."""
        s3_client = S3Client()
        with open(self.data_report_file_name, 'wb') as data_report_file:
            LOGGER.debug('Fetching enterprise completion report from S3')
            s3_client.get_enterprise_report(self.get_s3_csv_path(), data_report_file)
        return [data_report_file]

    def _generate_enterprise_report_progress_v2_csv(self):
        """Query the Enterprise Data API to get progress data to be turned into a CSV."""
        enrollments = EnterpriseDataApiClient().get_enterprise_enrollments(self.enterprise_customer_uuid)['results']
        if not enrollments:
            return []
        with open(self.data_report_file_name, 'w') as data_report_file:
            writer = csv.writer(data_report_file)
            writer.writerow(list(OrderedDict(sorted(enrollments[0].items())).keys()))
            for enrollment in enrollments:
                writer.writerow(list(OrderedDict(sorted(enrollment.items())).values()))
        return [data_report_file]

    def _generate_enterprise_report_progress_v3_csv(self):
        """Query the Enterprise Data V1 API to get progress data to be turned into a CSV."""
        enrollments = EnterpriseDataV1ApiClient().get_enterprise_enrollments(self.enterprise_customer_uuid)['results']
        if not enrollments:
            return []
        with open(self.data_report_file_name, 'w') as data_report_file:
            writer = csv.writer(data_report_file)
            csv_header = list(enrollments[0].keys())
            writer.writerow(csv_header)
            for enrollment in enrollments:
                writer.writerow(list(enrollment.values()))
        return [data_report_file]

    def _generate_enterprise_report_engagement_csv(self):
        """Query the Analytics Data API to get engagement data to be turned into a CSV."""
        engagements = AnalyticsDataApiClient().get_enterprise_engagements(self.enterprise_customer_uuid)['results']
        if not engagements:
            return []
        with open(self.data_report_file_name, 'w') as data_report_file:
            writer = csv.writer(data_report_file)
            writer.writerow(list(OrderedDict(sorted(engagements[0].items())).keys()))
            for engagement in engagements:
                writer.writerow(list(OrderedDict(sorted(engagement.items())).values()))
        return [data_report_file]

    def _generate_enterprise_report_progress_v2_json(self):
        """
        Query the Enterprise Data API to get progress data to be turned into json.
        """
        enrollments = EnterpriseDataApiClient().get_enterprise_enrollments(self.enterprise_customer_uuid)['results']
        report_data = enrollments if enrollments else []

        with open(self.data_report_file_name, 'w') as data_report_file:
            json.dump(report_data, data_report_file, indent=4)

        return [data_report_file]

    def _generate_enterprise_report_progress_v3_json(self):
        """
        Query the Enterprise Data V1 API to get progress data to be turned into json.
        """
        enrollments = EnterpriseDataV1ApiClient().get_enterprise_enrollments(self.enterprise_customer_uuid)['results']
        report_data = enrollments if enrollments else []

        with open(self.data_report_file_name, 'w') as data_report_file:
            json.dump(report_data, data_report_file, indent=4)

        return [data_report_file]

    def _generate_enterprise_report_catalog_csv(self):
        """
        Query the Enterprise Customer Catalog API and turn results into multiple CSV files.

        Note that at the current time, the CSV is unconventional. It is produced with multiple headers,
        one per each JSON object retrieved from the catalog API.
        """
        content_metadata = self.__get_content_metadata()
        LOGGER.debug('Grouping up content metadata by type...')
        grouped_content_metadata = {}
        for item in content_metadata:
            content_type = item['content_type']
            if content_type not in grouped_content_metadata:
                grouped_content_metadata[content_type] = [item]
            else:
                grouped_content_metadata[content_type].append(item)

        LOGGER.info('Beginning to write content metadata groups to CSVs...')
        files = []
        for content_type, grouped_items in list(grouped_content_metadata.items()):
            with open(self.data_report_file_name_with.format(content_type), 'w') as data_report_file:
                writer = csv.writer(data_report_file)
                if grouped_items:
                    # Write single row of headers in csv.
                    writer.writerow(generate_data(grouped_items[0], target='key'))

                for item in grouped_items:
                    writer.writerow(generate_data(item, target='value'))

                files.append(data_report_file)
        return files

    def _generate_enterprise_report_catalog_json(self):
        """Query the Enterprise Catalog API and transfer the results into a JSON file."""
        content_metadata = self.__get_content_metadata()
        with open(self.data_report_file_name, 'w') as data_report_file:
            json.dump(list(content_metadata), data_report_file, indent=4)
        return [data_report_file]

    def __get_content_metadata(self):
        """Get content metadata from the Enterprise Catalog API."""
        customer_catalogs = extract_catalog_uuids_from_reporting_config(self.reporting_config)
        enterprise_catalog_api_client = EnterpriseCatalogAPIClient()

        if not customer_catalogs.get('results'):
            customer_catalogs = enterprise_catalog_api_client.get_customer_catalogs(self.enterprise_customer_uuid)

        content_metadata = enterprise_catalog_api_client.get_content_metadata(customer_catalogs)
        return content_metadata
