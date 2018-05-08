# -*- coding: utf-8 -*-
"""
Tests for views in the `enterprise_data` module.
"""
from __future__ import absolute_import, unicode_literals

from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from test_utils import UserFactory


@mark.django_db
class TestEnterpriseEnrollmentsView(APITestCase):
    """
    Tests for EnterpriseEnrollmentsView
    """
    fixtures = ('enterprise_enrollment',)

    def setUp(self):
        super(TestEnterpriseEnrollmentsView, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('v0:enterprise_enrollments',
                           kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})

    def test_get_queryset_returns_enrollments(self):
        expected_result = {
            'count': 1,
            'num_pages': 1,
            'current_page': 1,
            'results': [{
                'enrollment_created_timestamp': '2014-06-27T16:02:38',
                'user_current_enrollment_mode': 'verified',
                'has_passed': True,
                'course_id': 'edX/Open_DemoX/edx_demo_course',
                'id': 2,
                'course_min_effort': 2,
                'course_start': '2016-09-01T00:00:00',
                'enterprise_user_id': 1,
                'course_title': 'All about acceptance testing!',
                'course_duration_weeks': '8',
                'course_pacing_type': 'instructor_paced',
                'user_username': 'test_user',
                'enterprise_sso_uid': 'harry',
                'enterprise_site_id': None,
                'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
                'course_end': '2016-12-01T00:00:00',
                'lms_user_id': 11,
                'enterprise_name': 'Enterprise 1',
                'letter_grade': 'Pass',
                'user_account_creation_timestamp': '2015-02-12T23:14:35',
                'passed_timestamp': '2017-05-09T16:27:34.690065',
                'course_max_effort': 4,
                'consent_granted': True,
                'user_email': 'test@example.com',
                'course_key': 'edX/Open_DemoX',
            }],
            'next': None,
            'start': 0,
            'previous': None
        }

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result == expected_result
