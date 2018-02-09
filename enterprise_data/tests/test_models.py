# -*- coding: utf-8 -*-
"""
Tests for the `enterprise-data` models module.
"""
import unittest

import ddt
from pytest import mark

from test_utils import EnterpriseEnrollmentFactory


@mark.django_db
@ddt.ddt
class TestEnterpriseEnrollment(unittest.TestCase):
    """
    Tests for Enterprise Enrollment model
    """

    def setUp(self):
        enterprise_user_id = 1234
        course_id = 'course-v1:edX+DemoX+DemoCourse'

        self.enrollment = EnterpriseEnrollmentFactory(enterprise_user_id=enterprise_user_id, course_id=course_id)
        super(TestEnterpriseEnrollment, self).setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = '<Enterprise Enrollment for user 1234 in course-v1:edX+DemoX+DemoCourse>'
        assert expected_str == method(self.enrollment)
