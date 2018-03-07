#!/usr/bin/python3
"""
Sends an Enterprise Customer's data file to a configured destination.
"""

from __future__ import absolute_import, unicode_literals

import argparse
import logging
import os
import re
import sys

from enterprise_reporting.clients.enterprise import EnterpriseAPIClient
from enterprise_reporting.reporter import EnterpriseReportSender, EnterpriseReportSenderFactory
from enterprise_reporting.utils import is_current_time_in_schedule

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def send_data(config):
    """
    Send data report to each enterprise.

    Args:
        config
    """
    enterprise_customer_name = config['enterprise_customer']['name']
    LOGGER.info('Kicking off job to send report for {}'.format(
        enterprise_customer_name
    ))

    try:
        reporter = EnterpriseReportSenderFactory.create(config)
        reporter.send_enterprise_report()
    except Exception:  # pylint: disable=broad-except
        exception_message = 'Data report failed to send for {enterprise_customer}'.format(
            enterprise_customer=enterprise_customer_name,
        )
        LOGGER.exception(exception_message)

    cleanup_files(config['enterprise_customer']['uuid'])
    LOGGER.info('Finished job to send report for {}'.format(
        enterprise_customer_name
    ))


def cleanup_files(enterprise_id):
    """
    Clean up any files created by sending the enterprise report.
    """
    directory = EnterpriseReportSender.FILE_WRITE_DIRECTORY
    pattern = r'{}'.format(enterprise_id)
    for f in os.listdir(directory):
        if re.search(pattern, f):
            os.remove(os.path.join(directory, f))


def process_reports():
    """
    Process and send reports based on the arguments passed.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--enterprise-customer', required=False, type=str,
                        help="EnterpriseCustomer UUID.")

    args = parser.parse_args()
    enterprise_api_client = EnterpriseAPIClient(
        os.environ.get('LMS_OAUTH_KEY'),
        os.environ.get('LMS_OAUTH_SECRET')
    )

    if args.enterprise_customer:
        reporting_configs = enterprise_api_client.get_enterprise_reporting_config(args.enterprise_customer)
    else:
        reporting_configs = enterprise_api_client.get_all_enterprise_reporting_configs()

    if args.enterprise_customer and not (reporting_configs and reporting_configs['results']):
        LOGGER.error('The enterprise {} does not have a reporting configuration.'.format(args.enterprise_customer))
        sys.exit(1)

    for reporting_config in reporting_configs['results']:
        LOGGER.info('Checking if reporting config for {} is ready for processing'.format(
            reporting_config['enterprise_customer']['name']
        ))
        if (args.enterprise_customer or
                is_current_time_in_schedule(
                    reporting_config['frequency'],
                    reporting_config['hour_of_day'],
                    reporting_config['day_of_month'],
                    reporting_config['day_of_week'])):
            send_data(reporting_config)


if __name__ == "__main__":
    process_reports()
    sys.exit(0)
