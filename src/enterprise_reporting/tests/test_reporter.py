"""
Test reporter.
"""
import datetime
import os
import unittest
from unittest import mock
from unittest.mock import MagicMock

import ddt
import pytest

from enterprise_reporting import reporter
from enterprise_reporting.reporter import EnterpriseReportSender
from enterprise_reporting.utils import encrypt_string


@ddt.ddt
class TestReporter(unittest.TestCase):
	""""
	Tests about reporter methods
	"""
	def setUp(self):
		self.FILE_WRITE_DIRECTORY = '/tmp'
		self.date = datetime.datetime.now().strftime("%Y-%m-%d")
		self.reporting_config = {
			'enterprise_customer': {
				'uuid': '12aacfee8ffa4cb3bed1059565a57f05', 'name': 'John'
			},
			'delivery_method': 'sftp',
			'data_type': 'catalog',
			'uuid': '987654321',
			'sftp_hostname': '127.0.0.1',
			'active': True,
			'report_type': 'json',
			'encrypted_password': 'bleeH-bLah-blUe001',
			'sftp_username': 'John1',
			'sftp_port': 22,
			'sftp_file_path': 'home/user/Documents',
			'encrypted_sftp_password': 'abraAcaDabradOo',
		}
		sftp_password = self.reporting_config['encrypted_sftp_password']
		self.reporting_config['encrypted_sftp_password'] = encrypt_string(sftp_password)

	@ddt.data(
		True,
		False
	)
	def test_data_report_file_name(self, flag_value):
		"""
		Tests if the report config file name is generated correctly when date is included
		"""
		self.reporting_config['include_date'] = flag_value
		enterprise_report_sender = EnterpriseReportSender.create(self.reporting_config)
		actual_file_name = enterprise_report_sender.data_report_file_name
		date_str = f"_{self.date}" if self.reporting_config.get('include_date') else ""
		expected_file_name = "{dir}/{enterprise_uuid}_{data_type}_{report_type}{date}.{report_type}".format(
			dir=self.FILE_WRITE_DIRECTORY,
			enterprise_uuid=self.reporting_config['enterprise_customer']['uuid'],
			data_type=self.reporting_config['data_type'],
			date=date_str,
			report_type=self.reporting_config['report_type']
		)
		assert actual_file_name == expected_file_name

	@ddt.data(
		'grade',
		'course_structure',
		'completion',
	)
	@mock.patch("enterprise_reporting.reporter.S3Client")
	def test_manual_reports(self, data_type, mock_s3_client):
		"""
		Verify that `get_enterprise_report` has been called with correct S3 CSV path.
		"""
		# mock S3Client get_enterprise_report to verify if it has called with correct arguments
		mock_s3_client.return_value.get_enterprise_report.return_value = MagicMock()

		report_config = dict(self.reporting_config, data_type=data_type, report_type="csv")
		enterprise_uuid = report_config['enterprise_customer']['uuid']

		# set environment variable
		s3_csv_path = f"BATMAN/REPORTS/{data_type}.csv"
		os.environ[f"{data_type}-{enterprise_uuid}"] = s3_csv_path

		enterprise_report_sender = EnterpriseReportSender.create(report_config)
		data_report_file = getattr(enterprise_report_sender, f'_generate_enterprise_report_{data_type}_csv')()

		mock_s3_client.return_value.get_enterprise_report.assert_called_with(s3_csv_path, data_report_file[0])

	@ddt.data(
		'grade',
		'course_structure',
		'completion',
	)
	@mock.patch("enterprise_reporting.reporter.S3Client")
	def test_manual_reports_without_env_var(self, data_type, mock_s3_client):
		"""
		Verify that `get_enterprise_report` raises correct exception if S3 csv path is not present as an env variable.
		"""
		# mock S3Client get_enterprise_report to verify if it has not called
		mock_s3_client.return_value.get_enterprise_report.return_value = MagicMock()

		report_config = dict(self.reporting_config, data_type=data_type, report_type="csv")
		enterprise_uuid = report_config['enterprise_customer']['uuid']

		# remove environment variable
		del os.environ[f"{data_type}-{enterprise_uuid}"]

		enterprise_report_sender = EnterpriseReportSender.create(report_config)
		with pytest.raises(ValueError) as ve:
			getattr(enterprise_report_sender, f'_generate_enterprise_report_{data_type}_csv')()

		assert ve.value.args[0] == 'Invalid S3 CSV path. Path: [None]'
		mock_s3_client.return_value.get_enterprise_report.assert_not_called()
