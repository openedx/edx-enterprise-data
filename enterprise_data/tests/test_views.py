# -*- coding: utf-8 -*-
"""
Tests for views in the `enterprise_data` module.
"""
from __future__ import absolute_import, unicode_literals

import mock
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from test_utils import UserFactory


@mark.django_db
class TestEnterpriseEnrollmentsViewSet(APITestCase):
    """
    Tests for EnterpriseEnrollmentsViewSet
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super(TestEnterpriseEnrollmentsViewSet, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        enterprise_api_client = mock.patch('enterprise_data.permissions.EnterpriseApiClient')
        self.enterprise_api_client = enterprise_api_client.start()
        self.addCleanup(enterprise_api_client.stop)

    def test_get_queryset_returns_enrollments(self):
        enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': enterprise_id
        }
        url = reverse('v0:enterprise-enrollments-list',
                      kwargs={'enterprise_id': enterprise_id})
        expected_result = {
            'count': 2,
            'num_pages': 1,
            'current_page': 1,
            'results': [{
                'enrollment_created_timestamp': '2014-06-27T16:02:38Z',
                'user_current_enrollment_mode': 'verified',
                'last_activity_date': '2017-06-23',
                'has_passed': True,
                'course_id': 'edX/Open_DemoX/edx_demo_course',
                'id': 2,
                'course_min_effort': 2,
                'course_start': '2016-09-01T00:00:00Z',
                'enterprise_user_id': 1,
                'user_country_code': 'US',
                'course_title': 'All about acceptance testing!',
                'course_duration_weeks': '8',
                'course_pacing_type': 'instructor_paced',
                'user_username': 'test_user',
                'enterprise_sso_uid': 'harry',
                'enterprise_site_id': None,
                'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
                'course_end': '2016-12-01T00:00:00Z',
                'lms_user_id': 11,
                'enterprise_name': 'Enterprise 1',
                'letter_grade': 'Pass',
                'user_account_creation_timestamp': '2015-02-12T23:14:35Z',
                'passed_timestamp': '2017-05-09T16:27:34.690065Z',
                'course_max_effort': 4,
                'consent_granted': True,
                'user_email': 'test@example.com',
                'course_key': 'edX/Open_DemoX',
                'coupon_name': 'Enterprise Entitlement Coupon',
                'coupon_code': 'PIPNJSUK33P7PTZH',
                'offer': 'Percentage, 100 (#1234)',
                'current_grade': 0.80,
                'course_price': '200.00',
                'discount_price': '120.00',
                'course_api_url': ('/enterprise/v1/enterprise-catalogs/ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
                                   '/courses/edX/Open_DemoX/edx_demo_course'),
            }, {
                'enrollment_created_timestamp': '2014-06-27T16:02:38Z',
                'user_current_enrollment_mode': 'verified',
                'last_activity_date': '2017-06-23',
                'has_passed': False,
                'course_id': 'edX/Open_DemoX/edx_demo_course',
                'id': 4,
                'course_min_effort': 2,
                'course_start': '2016-09-01T00:00:00Z',
                'enterprise_user_id': 3,
                'user_country_code': 'US',
                'course_title': 'All about acceptance testing!',
                'course_duration_weeks': '8',
                'course_pacing_type': 'instructor_paced',
                'user_username': 'test_user',
                'enterprise_sso_uid': 'harry',
                'enterprise_site_id': None,
                'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
                'course_end': '2016-12-01T00:00:00Z',
                'lms_user_id': 11,
                'enterprise_name': 'Enterprise 1',
                'letter_grade': None,
                'user_account_creation_timestamp': '2015-02-12T23:14:35Z',
                'passed_timestamp': None,
                'course_max_effort': 4,
                'consent_granted': True,
                'user_email': 'test@example.com',
                'course_key': 'edX/Open_DemoX',
                'coupon_name': 'Enterprise Entitlement Coupon',
                'coupon_code': 'PIPNJSUK33P7PTZH',
                'offer': 'Percentage, 100 (#1234)',
                'current_grade': 0.80,
                'course_price': '200.00',
                'discount_price': '120.00',
                'course_api_url': ('/enterprise/v1/enterprise-catalogs/ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
                                   '/courses/edX/Open_DemoX/edx_demo_course'),
            }],
            'next': None,
            'start': 0,
            'previous': None
        }

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result == expected_result

    def test_get_queryset_throws_error(self):
        enterprise_id = '0395b02f-6b29-42ed-9a41-45f3dff8349c'
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': enterprise_id
        }
        url = reverse('v0:enterprise-enrollments-list',
                      kwargs={'enterprise_id': enterprise_id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_overview_returns_overview(self):
        enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': enterprise_id
        }
        url = reverse('v0:enterprise-enrollments-overview',
                      kwargs={'enterprise_id': enterprise_id})
        expected_result = {
            'enrolled_learners': 2,
            'active_learners': {
                'past_week': 0,
                'past_month': 0,
            },
            'course_completions': 1,
            'last_updated_date': '2018-07-31T23:14:35Z',
            'number_of_users': 3,
        }

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result == expected_result

    def test_no_page_querystring_skips_pagination(self):
        enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': enterprise_id
        }
        url = reverse('v0:enterprise-enrollments-list',
                      kwargs={'enterprise_id': enterprise_id})
        url += '?no_page=true'
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # without pagination results are a list, not dict so we assert the data type and length
        assert isinstance(result, list)
        assert len(result) == 2
