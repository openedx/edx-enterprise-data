# -*- coding: utf-8 -*-
"""
External Resource Link Report Generation Code.
"""
from __future__ import absolute_import, unicode_literals

from collections import Counter
from datetime import date
import operator
import logging
import os
import re
import sys
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from py2neo import Graph

from enterprise_reporting.utils import send_email_with_attachment

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

AGGREGATE_REPORT_CSV_HEADER_ROW = u'Course Key,Course Title,Partner,External Domain,Count\n'
EXHAUSTIVE_REPORT_CSV_HEADER_ROW = u'Course Key,Course Title,Partner,External Links\n'


def create_csv_string(processed_results, header_row, additional_columns):
    """
    generates a string suitable to be written as a csv file. it will build
    upon the first string handed in via header_row

    processed_results - a dictionary with course keys as keys and a value that
                        also is a dict, containing keys for course_title and
                        organization (this will constitute the first 3 columns)
    header_row - a string suitable to be written to a csv file
               - must end with a newline
    additional_columns - a callable that takes a course data dict that can
                         return a csv string for any additional columns

    Returns (unicode) string
    """
    for course_key, data in processed_results.items():
        header_row += u'{},"{}",{},{}\n'.format(
            course_key,
            data['course_title'],
            data['organization'],
            additional_columns(data),
        )
    return header_row


def create_columns_for_aggregate_report(data):
    """
    Creates a csv string for additional columns in report
    """
    urls_sorted_by_counts = sorted(
        data['domain_count'].items(),
        key=operator.itemgetter(1),
        reverse=True
    )
    stringified_urls_and_counts = [
        u'{},{}'.format(url, count)
        for url, count in urls_sorted_by_counts
    ]
    return u'\n,,,'.join(stringified_urls_and_counts)


def create_columns_for_exhaustive_report(data):
    """
    Creates a csv string for additional columns in report
    """
    return u'\n,,,'.join(data['external_links'])


def gather_links_from_html(html_string):
    """
    Takes some html blob as a string and extracts any external links, and
    returns them as a set
    """
    pattern = 'https?://.*?[" <]'
    links = [
        link[0:-1].strip()
        for link in re.findall(pattern, html_string,)
        if (not link.lower().endswith('.png"') and
            not link.lower().endswith('.jpg"') and
            not link.lower().endswith('.jpeg"') and
            not link.lower().endswith('.gif"') and
            not '.edx.org' in link)
    ]
    return links


def process_coursegraph_results(raw_results):
    """
    Takes the data from a coursegraph query

    Returns a dict with course keys as the key and dict data about that course
    as value
    """
    processed_results = {}
    for entry in raw_results:
        course_key = entry['h.course_key']
        # Only want new style course keys to exclude archived courses
        if not course_key.startswith('course-'):
            continue

        external_links = gather_links_from_html(entry['h.data'])

        if not external_links:
            continue

        # Create entry in processed_results and keep external_links up to date
        if course_key not in processed_results:
            processed_results[course_key] = {
                'course_title': entry['course_title'],
                'organization': entry['organization'],
                'external_links': set(external_links),
                'domain_count': {},
            }
        else:
            processed_results[course_key]['external_links'].update(external_links)

        # Now use external links to create the domains and counts
        domains = [
            '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(link))
            for link in external_links
        ]
        # calculate the unique counts for all the urls
        domains_with_counts = dict(Counter(domains))

        for domain, count in domains_with_counts.items():
            if domain in processed_results[course_key]['domain_count']:
                processed_results[course_key]['domain_count'][domain] += count
            else:
                processed_results[course_key]['domain_count'][domain] = count

    return processed_results


def query_coursegraph():
    """
    Calls coursegraph with cypher query and returns query data

    The data is a list of dicts where each dict contains keys that correspond
    to what is being returned in the query
    """
    graph = Graph(
        bolt=True,
        http_port=os.environ.get('COURSEGRAPH_PORT'),
        host=os.environ.get('COURSEGRAPH_HOST'),
        secure=True,
    )
    query = '''MATCH
                (c:course)-[:PARENT_OF*]->(h:html) 
              WHERE 
                h.data =~ '.*https?://.*'
              RETURN
                c.display_name as course_title,
                c.org as organization,
                h.course_key, 
                h.data'''
    results = graph.run(query)
    return results.data()


def generate_and_email_report():
    """
    Generates a report an sends it as an email with an attachment
    """
    LOGGER.info("Querying Course Graph DB...")
    raw_results = query_coursegraph()
    processed_results = process_coursegraph_results(raw_results)

    LOGGER.info("Generating exhaustive external links spreadsheet...")
    exhaustive_report = create_csv_string(
        processed_results,
        EXHAUSTIVE_REPORT_CSV_HEADER_ROW,
        create_columns_for_exhaustive_report,
    )

    LOGGER.info("Generating aggregate external links spreadsheet...")
    aggregate_report = create_csv_string(
        processed_results,
        AGGREGATE_REPORT_CSV_HEADER_ROW,
        create_columns_for_aggregate_report
    )

    today = str(date.today())
    filenames = [
        'external-resource-link-report-{}.csv'.format(today),
        'external-resource-domain-report-{}.csv'.format(today)
    ]
    attachment_data = {
        filenames[0]: exhaustive_report.encode('utf-8'),
        filenames[1]: aggregate_report.encode('utf-8'),
    }

    subject = 'External Resource Link Report'
    body = '''Dear Customer Success,
Find attached a file containing course keys and their respective
external resource links.

If you have any questions/concerns with the report, please ask the
Enterprise Team (kindly)!

Sincerely,
The Enterprise Team'''

    from_email = os.environ.get('SEND_EMAIL_FROM')

    LOGGER.info("Emailing spreadsheets...")
    send_email_with_attachment(
        subject,
        body,
        from_email,
        TO_EMAILS.split(','),
        attachment_data
    )


if __name__ == '__main__':
    TO_EMAILS = sys.argv[1]
    generate_and_email_report()
