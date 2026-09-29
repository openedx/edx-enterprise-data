"""
Test send enterprise reports.
"""

import datetime
import unittest
from collections import namedtuple

import pytz

from enterprise_reporting.send_enterprise_reports import should_deliver_report
from enterprise_reporting.utils import FREQUENCY_TYPE_DAILY


class TestSendEnterpriseReports(unittest.TestCase):

	def test_should_deliver_report(self):
		"""
		Verify that `should_deliver_report` works.
		"""
		est_timezone = pytz.timezone('US/Eastern')
		current_est_time = datetime.datetime.now(est_timezone)
		reporting_config = {
			'active': True,
			'data_type': 'progress_v3',
			'frequency': FREQUENCY_TYPE_DAILY,
			'hour_of_day': current_est_time.hour,
			'day_of_month': current_est_time.day,
			'day_of_week': current_est_time.weekday(),
		}
		# these are passed from jenkins when we manually execute an enterprise report job
		# in case of automated jobs, these are empty
		Command = namedtuple("Command", "data_type enterprise_customer")
		args = Command('', '')

		assert should_deliver_report(args, reporting_config, current_est_time)
