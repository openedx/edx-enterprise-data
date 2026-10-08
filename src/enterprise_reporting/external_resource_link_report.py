"""
External Resource Link Report Generation Code.
"""


import logging
import operator
import os
import re
import sys
from collections import Counter
from datetime import date
from urllib.parse import urlparse

from py2neo import Graph

from enterprise_reporting.utils import send_email_with_attachment

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

AGGREGATE_REPORT_CSV_HEADER_ROW = 'Course Key,Course Title,Partner,External Domain,Count\n'


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
    for course_key, data in list(processed_results.items()):
        header_row += '{},"{}",{},{}\n'.format(
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
        list(data['domain_count'].items()),
        key=operator.itemgetter(1),
        reverse=True
    )
    stringified_urls_and_counts = [
        f'{url},{count}'
        for url, count in urls_sorted_by_counts
    ]
    return '\n,,,'.join(stringified_urls_and_counts)


def gather_links_from_html(html_string):
    """
    Takes some html blob as a string and extracts any external links, and
    returns them as a set
    """
    pattern = 'https?://.*?[" <]'

    links = []
    for link in re.findall(pattern, html_string,):
        link = link[0:-1].strip()
        if (link.lower().endswith('.png"') or
            link.lower().endswith('.jpg"') or
            link.lower().endswith('.jpeg"') or
            link.lower().endswith('.gif"') or
            '.edx.org' in link):
            continue

        # Want to verify the link captured is a proper url
        # If not, toss it out and throw a log message
        try:
            urlparse(link)
        except ValueError:
            LOGGER.warning(
                "Unparsable URL found. Not including in report: %s" % link
            )
            continue

        links.append(link)
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

        for domain, count in list(domains_with_counts.items()):
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
              WHERE (
                h.data CONTAINS 'https://'
                OR
                h.data CONTAINS 'http://'
              )
              RETURN
                c.display_name as course_title,
                c.org as organization,
                h.course_key, 
                h.data'''
    results = graph.run(query)
    return results.data()


def split_up_results(processed_results_part1):
    """
    Splits up a dictionary of processed_results into a list of
    two smaller dictionaries.
    """
    # NOTE: we are splitting this into 2 dicts because it is 1) easy to do
    # and 2) we have about 8 MB of overhead for newly added strings to this
    # report before it becomes a problem again... which should not be for
    # a veeeery long time.
    #
    # If emails fail due to size in the future, implement a solution that
    # dynamically chooses chunk size and email quantity based on size of
    # string data included in each of the dictionary entries being
    # iterated over.
    processed_results_part2 = {}

    original_len = len(processed_results_part1)
    while len(processed_results_part1) > (original_len / 2):
        k, v = processed_results_part1.popitem()
        processed_results_part2[k] = v

    return [processed_results_part1, processed_results_part2]


def generate_and_email_report():
    """
    Generates a report an sends it as an email with an attachment
    """

    from_email = os.environ.get('SEND_EMAIL_FROM')
    today = str(date.today())
    subject = 'External Resource Link Report'
    body = '''Dear Customer Success,
Find attached a file containing course keys and their respective
external resource links.

If you have any questions/concerns with the report, please ask the
Enterprise Team!

Sincerely,
The Enterprise Team'''

    LOGGER.info("Querying Course Graph DB...")
    raw_results = query_coursegraph()

    # Results are too large to send in 1 email (~10MB is the limit) so
    # we split up the results into two parts
    processed_results = process_coursegraph_results(raw_results)
    result_dicts = split_up_results(processed_results)

    for index, result in enumerate(result_dicts):
        readable_number = index + 1

        LOGGER.info(
            "Generating aggregate external links spreadsheet part %s..." % readable_number
        )
        aggregate_report_data = create_csv_string(
            result,
            AGGREGATE_REPORT_CSV_HEADER_ROW,
            create_columns_for_aggregate_report
        )
        filename = 'external-resource-domain-report-part{}-{}.csv'.format(
            readable_number,
            today,
        )
        attachment_data = {filename: aggregate_report_data.encode('utf-8')}

        LOGGER.info(
            "Emailing aggregate spreadsheet part %s..." % readable_number
        )
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
