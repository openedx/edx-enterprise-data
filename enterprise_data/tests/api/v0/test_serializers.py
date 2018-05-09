# -*- coding: utf-8 -*-
"""
Tests for the `edx-enterprise` serializer module.
"""

from __future__ import absolute_import, unicode_literals

from pytest import mark, raises
from rest_framework.test import APITestCase

from enterprise_data.api.v0.serializers import EnterpriseEnrollmentSerializer


@mark.django_db
class TestEnterpriseEnrollmentSerializer(APITestCase):
    """
    Tests for `enterprise_enrollment` API serializer.
    """

    def setUp(self):
        super(TestEnterpriseEnrollmentSerializer, self).setUp()

        self.enrollment_data = {
            "id": 2,
            "enterprise_id": "ee5e6b3a-069a-4947-bb8d-d2dbc323396c",
            "enterprise_name": "Enterprise 1",
            "lms_user_id": 11,
            "enterprise_user_id": 1,
            "course_id": "edX/Open_DemoX/edx_demo_course",
            "enrollment_created_timestamp": "2014-06-27T16:02:38Z",
            "user_current_enrollment_mode": "verified",
            "consent_granted": 1,
            "letter_grade": "Pass",
            "has_passed": 1,
            "passed_timestamp": "2017-05-09T16:27:34.690065Z",
            "enterprise_sso_uid": "harry",
            "course_title": "All about acceptance testing!",
            "course_start": "2016-09-01T00:00:00Z",
            "course_end": "2016-12-01T00:00:00Z",
            "course_pacing_type": "instructor_paced",
            "course_duration_weeks": "8",
            "course_min_effort": 2,
            "course_max_effort": 4,
            "user_account_creation_timestamp": "2015-02-12T23:14:35Z",
            "user_email": "test@example.com",
            "user_username": "test_user",
            "course_key": "edX/Open_DemoX"
        }

    def test_enrollment_serialization(self):
        expected_serialized_data = {
            'id': 2,
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'enterprise_name': 'Enterprise 1',
            'lms_user_id': 11,
            'enterprise_user_id': 1,
            'course_id': 'edX/Open_DemoX/edx_demo_course',
            'enrollment_created_timestamp': '2014-06-27T16:02:38Z',
            'user_current_enrollment_mode': 'verified',
            'consent_granted': True,
            'letter_grade': 'Pass',
            'has_passed': True,
            'course_min_effort': 2,
            'course_start': '2016-09-01T00:00:00Z',
            'course_title': 'All about acceptance testing!',
            'course_duration_weeks': '8',
            'course_pacing_type': 'instructor_paced',
            'enterprise_sso_uid': 'harry',
            'course_end': '2016-12-01T00:00:00Z',
            'user_account_creation_timestamp': '2015-02-12T23:14:35Z',
            'passed_timestamp': '2017-05-09T16:27:34.690065Z',
            'course_max_effort': 4,
            'user_email': 'test@example.com',
            'user_username': 'test_user',
            'course_key': 'edX/Open_DemoX'
        }
        serializer = EnterpriseEnrollmentSerializer(self.enrollment_data)
        assert serializer.data == expected_serialized_data
