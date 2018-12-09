#!/usr/bin/python3
"""
Export edx data (mysql or vertica) into a csv file.

This script provides the framework for querying the edxapp mysql database
or the Vertica-based data warehouse and outputting the result of your
query to a CSV file.

This is useful for analyzing data contained in these data sources
and sharing your analysis with others.

To run this script:

1. Create edx-enterprise-data virtualenv.
2. Install python requirements with `pip install -r requirements/dev.txt`.
3. Set environment variables required by mysql-connector:
    $ export MYSQLXPB_PROTOBUF_INCLUDE_DIR=/usr/local/opt/protobuf/include
    $ export MYSQLXPB_PROTOBUF_LIB_DIR=/usr/local/opt/protobuf/lib
    $ export MYSQLXPB_PROTOC=/usr/local/opt/protobuf/bin/protoc
4. Set environment variables required to connect to mysql:
    $ export MYSQL_HOST=[mysql hostname]
    $ export MYSQL_USERNAME=[mysql username]
    $ export MYSQL_PASSWORD=[mysql password]
    $ export MYSQL_DATABASE=[mysql database name]
5. Run `python enterprise_reporting/export_edxapp_data.py`.
6. Find CSV output in the .output directory at the root of this repository.
"""
from __future__ import absolute_import, unicode_literals

import csv
import datetime
import logging
import os
import sys
from io import open  # pylint: disable=redefined-builtin

import mysql.connector
import vertica_python

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

MISSING_ENROLLMENT_QUERY = '''
    SELECT
        u.id,
        u.username,
        u.email,
        ec.name AS enterprise_name,
        sce.course_id,
        sce.mode,
        sce.created AS course_enrollment_created,
        ecu.created AS enterprise_link_created,
        u.date_joined AS edx_account_created
    FROM
        enterprise_enterprisecustomeruser ecu
    JOIN
        enterprise_enterprisecustomer ec
    ON
        ecu.enterprise_customer_id = ec.uuid
    JOIN
        auth_user u
    ON
        ecu.user_id = u.id AND
        u.email NOT LIKE '%@edx.org'
    JOIN
        student_courseenrollment sce
    ON
        ecu.user_id = sce.user_id AND
        ecu.created <= sce.created
    LEFT JOIN
        enterprise_enterprisecourseenrollment ece
    ON
        ecu.id = ece.enterprise_customer_user_id
    WHERE
        ece.id IS NULL
    ORDER BY
        ec.name,
        sce.created DESC;
'''


def export_data(data, report_name_prefix):
    """
    Export given data to a csv report.
    """
    if data:
        now = datetime.datetime.now()
        output_dir = '.output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        csv_filename = '{}/{}_{}.csv'.format(
            output_dir,
            report_name_prefix,
            now.strftime('%Y%m%d%H%M')
        )
        header = data[0].keys()
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for row in data:
                for key, value in row.items():
                    if isinstance(value, datetime.datetime):
                        row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        row[key] = str(value)
                writer.writerow(row.values())


def fetch_lms_data(query):
    """
    Return the results of the given query against a mysql database.

    Uses the following environment variables to connnect to the database:
    MYSQL_HOST, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_DATABASE
    """
    data = []
    connection_info = {
        'host': os.environ.get('MYSQL_HOST'),
        'user': os.environ.get('MYSQL_USERNAME'),
        'password': os.environ.get('MYSQL_PASSWORD'),
        'database': os.environ.get('MYSQL_DATABASE'),
    }
    try:
        connection = mysql.connector.connect(**connection_info)
        cur = connection.cursor(dictionary=True)
        cur.execute(query)
        for row in cur:
            data.append(row)
    finally:
        connection.close()
    return data


def fetch_vertica_data(query):
    """
    Return the results of the given query against a vertica database.

    Uses the following environment variables to connnect to the database:
    VERTICA_HOST, VERTICA_USERNAME, VERTICA_PASSWORD, VERTICA_DATABASE
    """
    connection_info = {
        'host': os.environ.get('VERTICA_HOST'),
        'user': os.environ.get('VERTICA_USERNAME'),
        'password': os.environ.get('VERTICA_PASSWORD'),
        'database': os.environ.get('VERTICA_DATABASE'),
    }
    with vertica_python.connect(**connection_info) as connection:
        cur = connection.cursor('dict')
        cur.execute(query)
        return cur.fetchall()


def export_missing_enterprise_enrollments():
    """
    Find and export missing enterprise enrollments.

    Run query to find course enrollments which could potentially be
    considered Enterprise enrollments, but are not currently recorded
    as such.
    """
    missing_enterprise_enrollments = fetch_lms_data(MISSING_ENROLLMENT_QUERY)
    if missing_enterprise_enrollments:
        export_data(missing_enterprise_enrollments, 'missing_enterprise_enrollments')


if __name__ == "__main__":
    export_missing_enterprise_enrollments()
    sys.exit(0)
