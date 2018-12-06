# -*- coding: utf-8 -*-
"""
External Resource Link Report Generation Code.
"""
from __future__ import absolute_import, unicode_literals

import logging
import os
import re
import sys
from datetime import date

from py2neo import Graph

from enterprise_reporting.utils import send_email_with_attachment

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def generate_csv_string(processed_results):
    """
    Takes a dict of processed results and turns it into a string suitable
    to be written as a csv file

    Returns (unicode) string
    """
    csv_string = u'Course Key,Course Title,Partner,External Links\n'
    for course_key, data in processed_results.items():
        links = u'\n,,,'.join(data['external_links'])
        csv_string += u'{},"{}",{},{}\n'.format(
            course_key,
            data['course_title'],
            data['organization'],
            links,
        )
    return csv_string


def gather_links_from_html(html_string):
    """
    Takes some html blob as a string and extracts any external links, and
    returns them as a set
    """
    pattern = 'https?://.*?[" <]'
    links = set([
        link[0:-1]
        for link in re.findall(pattern, html_string,)
        if (not link.lower().endswith('.png"') and
            not link.lower().endswith('.jpg"') and
            not link.lower().endswith('.jpeg"') and
            not link.lower().endswith('.gif"') and
            not '.edx.org' in link)
    ])
    return links


def process_results(raw_results):
    """
    Takes the data from a coursegraph query

    Returns a dict with course keys as the key and list data about that course
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

        if course_key not in processed_results:
            processed_results[course_key] = {
                'course_title': entry['course_title'],
                'organization': entry['organization'],
                'external_links': external_links,
            }
        else:
            processed_results[course_key]['external_links'].update(external_links)
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

    LOGGER.info("Processing {} html blobs returned...".format(len(raw_results)))
    processed_results = process_results(raw_results)

    LOGGER.info("Generating spreadsheet...")
    csv_string = generate_csv_string(processed_results)

    subject = 'External Resource Link Report'
    body = '''Dear Customer Success,
Find attached a file containing course keys and their respective
external resource links.

If you have any questions/concerns with the report, please ask the
Enterprise Team (kindly)!

Sincerely,
The Enterprise Team'''

    from_email = os.environ.get('SEND_EMAIL_FROM')
    filename = 'external-resource-link-report-{}.csv'.format(str(date.today()))

    LOGGER.info("Emailing spreadsheet...")
    send_email_with_attachment(
        subject,
        body,
        from_email,
        TO_EMAILS.split(','),
        filename,
        attachment_data=csv_string.encode('utf-8')
    )


if __name__ == '__main__':
    TO_EMAILS = sys.argv[1]
    generate_and_email_report()
