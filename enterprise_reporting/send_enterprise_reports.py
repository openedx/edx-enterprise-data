#!/usr/bin/python3
"""
Sends an Enterprise Customer's data file to a configured destination.
"""


import argparse
import datetime
import logging
import os
import re
import sys

import pytz

from enterprise_reporting.clients.enterprise import EnterpriseAPIClient
from enterprise_reporting.reporter import EnterpriseReportSender
from enterprise_reporting.utils import is_current_time_in_schedule

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
DATA_TYPES = ['progress', 'progress_v2', 'progress_v3', 'catalog', 'grade', 'course_structure', 'completion', 'engagement']


def send_data(config):
    """
    Send data report to each enterprise.

    Args:
        config
    """
    enterprise_customer_name = config['enterprise_customer']['name']
    LOGGER.info(f'Kicking off job to send report for {enterprise_customer_name}')

    error_raised = False
    try:
        reporter = EnterpriseReportSender.create(config)
        reporter.send_enterprise_report()
    except Exception:  # pylint: disable=broad-except
        error_raised = True
        LOGGER.exception(f'Data report failed to send for {enterprise_customer_name}')

    cleanup_files(config['enterprise_customer']['uuid'])
    LOGGER.info(f'Finished job to send report for {enterprise_customer_name}')

    return error_raised


def cleanup_files(enterprise_id):
    """
    Clean up any files created by sending the enterprise report.
    """
    directory = EnterpriseReportSender.FILE_WRITE_DIRECTORY
    pattern = fr'{enterprise_id}'
    for f in os.listdir(directory):
        if re.search(pattern, f):
            os.remove(os.path.join(directory, f))


def should_deliver_report(args, reporting_config, current_est_time):
    """Given CLI arguments and the reporting configuration, determine if delivery should happen."""
    valid_data_type = reporting_config['data_type'] in (args.data_type or DATA_TYPES)
    enterprise_customer_specified = bool(args.enterprise_customer)

    meets_schedule_requirement = is_current_time_in_schedule(
        current_est_time,
        reporting_config['frequency'],
        reporting_config['hour_of_day'],
        reporting_config['day_of_month'],
        reporting_config['day_of_week']
    )
    LOGGER.info("Report Delivery Logic. Active: [%s], ValidDataType: [%s], MeetSchedule: [%s], EnterpriseInArgs: [%s]",
        reporting_config['active'],
        valid_data_type,
        meets_schedule_requirement,
        enterprise_customer_specified,
    )

    return reporting_config['active'] and \
           valid_data_type and \
           (enterprise_customer_specified or meets_schedule_requirement)


def process_reports():
    """
    Process and send reports based on the arguments passed.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--enterprise-customer', required=False, type=str,
                        help="Enterprise Customer's UUID. If specified, data delivery is forced.")
    parser.add_argument('-d', '--data-type', required=False, type=str, choices=DATA_TYPES,
                        help="Data type. If specified, only this type of data for the customer(s) will be sent, "
                             "whether forced or not.")
    parser.add_argument('--page-size', required=False, type=int, default=1000,
                        help="The page size to use to retrieve data that comes in a paginated response.")
    args = parser.parse_args()

    enterprise_api_client = EnterpriseAPIClient()
    if args.enterprise_customer:
        reporting_configs = enterprise_api_client.get_enterprise_reporting_configs(args.enterprise_customer)
    else:
        reporting_configs = enterprise_api_client.get_all_enterprise_reporting_configs()

    if args.enterprise_customer and not (reporting_configs and reporting_configs['results']):
        LOGGER.error(f'The enterprise {args.enterprise_customer} does not have a reporting configuration.')
        sys.exit(1)

    # We are defining the current est time globally because we want the current time for a job
    # to remain same thoughout the job. This ensures that a single report is not processed multiple times. 
    # See this comment for more details: https://2u-internal.atlassian.net/browse/ENT-9954?focusedCommentId=5356815
    est_timezone = pytz.timezone('US/Eastern')
    current_est_time = datetime.datetime.now(est_timezone)

    error_raised = False
    for reporting_config in reporting_configs['results']:
        LOGGER.info('Checking if {}\'s reporting config for {} data in {} format is ready for processing'.format(
            reporting_config['enterprise_customer']['name'],
            reporting_config['data_type'],
            reporting_config['report_type'],
        ))

        if should_deliver_report(args, reporting_config, current_est_time):
            if send_data(reporting_config):
                error_raised = True
        else:
            LOGGER.info('Not ready -- skipping this report.')

    if error_raised:
        LOGGER.error(
            'One or more reports in this job were not successfully sent to customers. '
            'Please check these jenkins logs for more information.'
        )
        sys.exit(1)

if __name__ == "__main__":
    process_reports()
    sys.exit(0)
