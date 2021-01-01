"""
Test reporter.
"""
import unittest
import datetime
import pytest
import ddt

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
				'uuid': '4815162242', 'name': 'John'
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
