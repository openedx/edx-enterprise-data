"""
Test utils for external link reports.
"""

import unittest
from collections import OrderedDict

from enterprise_reporting.external_resource_link_report import (
    AGGREGATE_REPORT_CSV_HEADER_ROW,
    create_columns_for_aggregate_report,
    create_csv_string,
    process_coursegraph_results,
    split_up_results,
)


class TestUtilsCoursegraph(unittest.TestCase):
    
    def setUp(self):
        """
        Setup reusable test data
        """
        self.raw_data = [
            {'course_title': 'course1',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test1',
             'h.data': '<span href="http://www.google.com">my site</span>'},
            {'course_title': 'course1',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test1',
             'h.data': '<span href="http://www.google.com">my site is http://www.google.com</span>'},
            {'course_title': 'course1',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test1',
             'h.data': '<span href="http://www.facebook.com/">my site</span>'},
            
            {'course_title': 'course2',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test2',
             'h.data': '<span href="http://www.google2.com/">my site</span>'},
            {'course_title': 'course2',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test2',
             'h.data': '<span href="http://www.google2.com">my site</span>'},
            {'course_title': 'course2',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test2',
             'h.data': '<span href="http://www.google2.com/someextension/">my site</span>'},
            {'course_title': 'course2',
             'organization': 'edx',
             'h.course_key': 'course-v1:I+am+a+test2',
             'h.data': '<span href="http://www.google2.com/someextension/">my site</span>'},
            
            {'course_title': 'course3',
             'organization': 'edx2',
             'h.course_key': 'course-v1:I+am+a+test3',
             'h.data': '<span href="http://www.google3.com">my site</span>'},
    
            {'course_title': 'course4',
             'organization': 'edx2',
             'h.course_key': 'course-v1:I+am+a+test4',
             'h.data': 'I have no urls'},
            {'course_title': 'course4',
             'organization': 'edx2',
             'h.course_key': 'course-v1:I+am+a+test4+with+bad+url',
             'h.data': '<p>code choking on https://[Web App Name].scm.azureWeb Apps.net</p>'},

            {'course_title': 'oldcourse',
             'organization': 'oldx2',
             'h.course_key': 'oldx2course:I+am+a+test+for+old+coursekeys',
             'h.data': '<span href="http://www.google3.com">my site</span>'},

        ]

    def test_process_coursegraph_results(self):
        """
        process_results should properly structure the data in a dictionary returned
        """
        expected = {
            'course-v1:I+am+a+test1': {
                'course_title': 'course1',
                'organization': 'edx',
                'external_links': {
                    'http://www.google.com',
                    'http://www.facebook.com/'
                },
                'domain_count': {
                    'http://www.google.com': 3,
                    'http://www.facebook.com': 1,
                },
            },
            'course-v1:I+am+a+test2': {
                'course_title': 'course2',
                'organization': 'edx',
                'external_links': {
                    'http://www.google2.com/',
                    'http://www.google2.com',
                    'http://www.google2.com/someextension/',
                },
                'domain_count': {
                    'http://www.google2.com': 4,
                },
            },
            'course-v1:I+am+a+test3': {
                'course_title': 'course3',
                'organization': 'edx2',
                'external_links': {'http://www.google3.com'},
                'domain_count': {
                    'http://www.google3.com': 1,
                },
            },
        }
        assert process_coursegraph_results(self.raw_data) == expected

    def test_split_up_results(self):
        """
        split_up_results should take a dictionary of process results and split
        it into a list of smaller dictionaries.
        """
        processed_results = OrderedDict([
            ('course-v1:I+am+a+test1', {
                'course_title': 'course1',
                'organization': 'edx',
                'domain_count': OrderedDict([
                    ('http://www.google.com', 2),
                    ('http://www.facebook.com', 1),
                ]),
            }),
            ('course-v1:I+am+a+test2', {
                'course_title': 'course2',
                'organization': 'edx',
                'domain_count': {'http://www.google2.com': 4},
            }),
            ('course-v1:I+am+a+test3', {
                'course_title': 'course3',
                'organization': 'edx2',
                'domain_count': {'http://www.google3.com': 1},
            }),
        ])

        results_list = split_up_results(processed_results)

        assert len(results_list) == 2
        assert len(results_list[0]) == 1
        assert len(results_list[1]) == 2

    def test_create_aggregate_report_csv_string(self):
        """
        generate_aggregate_report_csv_string should create the expected csv
        string given some processed results
        """

        processed_results = OrderedDict([
            ('course-v1:I+am+a+test1', {
                'course_title': 'course1',
                'organization': 'edx',
                'domain_count': OrderedDict([
                    ('http://www.google.com', 2),
                    ('http://www.facebook.com', 1),
                ]),
            }),
            ('course-v1:I+am+a+test2', {
                'course_title': 'course2',
                'organization': 'edx',
                'domain_count': {'http://www.google2.com': 4},
            }),
            ('course-v1:I+am+a+test3', {
                'course_title': 'course3',
                'organization': 'edx2',
                'domain_count': {'http://www.google3.com': 1},
            }),
        ])
        expected = (
            'Course Key,Course Title,Partner,External Domain,Count\n'
            'course-v1:I+am+a+test1,"course1",edx,http://www.google.com,2\n'
            ',,,http://www.facebook.com,1\n'
            'course-v1:I+am+a+test2,"course2",edx,http://www.google2.com,4\n'
            'course-v1:I+am+a+test3,"course3",edx2,http://www.google3.com,1\n'
        )
        actual = create_csv_string(
            processed_results,
            AGGREGATE_REPORT_CSV_HEADER_ROW,
            create_columns_for_aggregate_report,
        )
        assert actual == expected
