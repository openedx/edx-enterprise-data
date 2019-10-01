# -*- coding: utf-8 -*-
"""
Test reporter.
"""
import unittest
import datetime

from enterprise_reporting import reporter
from enterprise_reporting.reporter import EnterpriseReportSender
from enterprise_reporting.utils import encrypt_string


class TestReporter(unittest.TestCase):

	def setUp(self):
		self.FILE_WRITE_DIRECTORY = '/tmp'
		self.date = datetime.datetime.now().strftime("%Y-%m-%d")

	def test_data_report_file_name_with_date(self):
		reporting_config = {
			'enterprise_customer': {
				'uuid': '12345678910', 'name': 'John'
			},
			'delivery_method': 'sftp', 'data_type': 'catalog', 'uuid': '987654321', 'sftp_hostname': '127.0.0.1', 'active': True,
			'report_type': 'json', 'encrypted_password': 'bleeH-bLah-blUe001', 'sftp_username': 'John1', 'sftp_port': 22,
			'sftp_file_path': 'home/user/Documents', 'encrypted_sftp_password': 'abraAaaa-caDabraa-doOooo', 'include_date': True
		}

		sftp_password = reporting_config['encrypted_sftp_password']
		reporting_config['encrypted_sftp_password'] = encrypt_string(sftp_password)
		enterprise_reporter = EnterpriseReportSender.create(reporting_config)
		actual_file_name = enterprise_reporter.data_report_file_name
		expected_name = "{dir}/{enterprise_uuid}_{data_type}_{report_type}_{date}.{report_type}".format(
			dir=self.FILE_WRITE_DIRECTORY,
			enterprise_uuid=reporting_config['enterprise_customer']['uuid'],
			data_type=reporting_config['data_type'],
			date=self.date,
			report_type=reporting_config['report_type']
			)
		assert actual_file_name == expected_name

	def test_data_report_file_name_without_date(self):
		reporting_config = {
			'enterprise_customer': {
				'uuid': '4815162342', 'name': 'Amy'
			},
			'delivery_method': 'sftp', 'data_type': 'catalog', 'uuid': '42135342-12345', 'sftp_hostname': '127.0.0.1', 'active': True,
			'report_type': 'csv', 'encrypted_password': 'bleeH-bLah-blUe001', 'sftp_username': 'Amy22', 'sftp_port': 80,
			'sftp_file_path': 'home/user/Documents', 'encrypted_sftp_password': 'abraAaaa-caDabraa-doOooo',
			'include_date': False
		}
		sftp_password = reporting_config['encrypted_sftp_password']
		reporting_config['encrypted_sftp_password'] = encrypt_string(sftp_password)
		enterprise_reporter = EnterpriseReportSender.create(reporting_config)
		actual_file_name = enterprise_reporter.data_report_file_name
		expected_name = "{dir}/{enterprise_uuid}_{data_type}_{report_type}.{report_type}".format(
			dir=self.FILE_WRITE_DIRECTORY,
			enterprise_uuid=reporting_config['enterprise_customer']['uuid'],
			data_type=reporting_config['data_type'],
			date=self.date,
			report_type=reporting_config['report_type']
		)
		assert actual_file_name == expected_name
