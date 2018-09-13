# -*- coding: utf-8 -*-
"""
Tests for views in the `enterprise_data` module.
"""
from __future__ import absolute_import, unicode_literals

from datetime import date, datetime, timedelta

import ddt
import mock
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django.utils import timezone

from enterprise_data.api.v0.views import subtract_one_month
from enterprise_data.permissions import HasDataAPIDjangoGroupAccess
from test_utils import EnterpriseEnrollmentFactory, EnterpriseUserFactory, UserFactory


@ddt.ddt
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
                'enterprise_user': 111,
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
                'enterprise_user': 333,
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

    def test_get_queryset_returns_enrollments_with_passed_date_filter(self):
        enterprise_id = '413a0720-3efe-4cf5-98c8-3b4e42d3c501'
        url = u"{url}?passed_date=last_week".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id})
        )

        enterprise_user = EnterpriseUserFactory(enterprise_user_id=1234)

        date_today = date.today()
        in_past_week_passed_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_passed_dates = [date_today - timedelta(weeks=2)]
        passed_dates = in_past_week_passed_dates + before_past_week_passed_dates
        for index, passed_date in enumerate(passed_dates):
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise_user,
                enterprise_id=enterprise_id,
                user_email='user{}@example.com'.format(index),
                passed_timestamp=passed_date,
                course_title='course101',
                has_passed=True,
                consent_granted=True,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == len(in_past_week_passed_dates)
        for enrollment, passed_date in zip(result['results'], in_past_week_passed_dates):
            assert enrollment['has_passed'] is True
            assert datetime.strptime(enrollment['passed_timestamp'], "%Y-%m-%dT%H:%M:%SZ").date() == passed_date

    @ddt.data(
        (
            'active_past_week',
            [date.today(), date.today() - timedelta(days=2)]
        ),
        (
            'inactive_past_week',
            [date.today() - timedelta(weeks=2), subtract_one_month(date.today())]
        ),
        (
            'inactive_past_month',
            [subtract_one_month(date.today())]
        )
    )
    @ddt.unpack
    def test_get_queryset_returns_enrollments_with_learner_activity_filter(self, activity_filter, expected_dates):
        enterprise_id = '413a0720-3efe-4cf5-98c8-3b4e42d3c509'
        url = u"{url}?learner_activity={activity_filter}".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id}),
            activity_filter=activity_filter
        )

        enterprise_user = EnterpriseUserFactory(enterprise_user_id=1234)

        date_today = date.today()
        in_past_week_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_dates = [date_today - timedelta(weeks=2)]
        before_past_month_dates = [subtract_one_month(date.today())]
        activity_dates = in_past_week_dates + before_past_week_dates + before_past_month_dates
        for activity_date in activity_dates:
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise_user,
                enterprise_id=enterprise_id,
                last_activity_date=activity_date,
                consent_granted=True,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == len(expected_dates)
        for enrollment in result['results']:
            assert datetime.strptime(enrollment['last_activity_date'], "%Y-%m-%d").date() in expected_dates

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


@mark.django_db
class TestEnterpriseUsersViewSet(APITestCase):
    """
    Tests for EnterpriseUsersViewSet
    """

    def setUp(self):
        super(TestEnterpriseUsersViewSet, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        enterprise_api_client = mock.patch('enterprise_data.permissions.EnterpriseApiClient')
        self.enterprise_api_client = enterprise_api_client.start()
        self.addCleanup(enterprise_api_client.stop)

        one_day = timedelta(days=1)
        date_in_past = timezone.now() - one_day
        date_in_future = timezone.now() + one_day

        # Users without enrollments
        EnterpriseUserFactory(
            enterprise_user_id=1,
        )
        EnterpriseUserFactory(
            enterprise_user_id=2,
        )
        EnterpriseUserFactory(
            enterprise_user_id=3,
        )
        # Users to be assigned enrollments
        self.ent_user4 = EnterpriseUserFactory(
            enterprise_user_id=4,
        )
        self.ent_user5 = EnterpriseUserFactory(
            enterprise_user_id=5,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_past,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_future,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user5,
            course_end=date_in_future,
        )

    def test_viewset_no_query_params(self):
        """
        EnterpriseUserViewset should return all users if no filtering query
        params are present
        """
        url = reverse('v0:enterprise-users-list',
                      kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})
        response = self.client.get(url)
        assert response.json()['count'] == 5

    @mock.patch('enterprise_data.api.v0.views.EnterpriseUsersViewSet.paginate_queryset')
    def test_viewset_no_query_params_no_pagination(self, mock_paginate):
        """
        EnterpriseUserViewset should return all users if no filtering query
        params are present in a list if no pagination occurs
        """
        mock_paginate.return_value = None
        url = reverse('v0:enterprise-users-list',
                      kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})
        response = self.client.get(url)
        assert 'count' not in response.json()
        assert len(response.json()) == 5

    def test_viewset_filter_has_enrollments_true(self):
        """
        EnterpriseUserViewset should return all users that have enrollments
        if query param value is 'true'
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'has_enrollments': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 2

    def test_viewset_filter_has_enrollments_false(self):
        """
        EnterpriseUserViewset should return all users that do not have
        enrollments if query param value is 'false'
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'has_enrollments': 'false', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 3

    def test_viewset_filter_has_enrollments_garbled(self):
        """
        EnterpriseUserViewset should not filter users returned if the value
        for has_enrollments query param is not a 'true' or 'false'
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'has_enrollments': 'asdiqwjodijacvasd', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 5

    def test_viewset_filter_active_courses_true(self):
        """
        EnterpriseUserViewset should filter out enrollments for courses that
        have a course_end date in the past if active_courses query param
        value is true
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'active_courses': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 2

    def test_viewset_filter_active_courses_false(self):
        """
        EnterpriseUserViewset should filter out enrollments for courses that
        have a course_end date in the future if active_courses query param
        value is true
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'active_courses': 'false', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 1

    def test_viewset_enrollment_count_present(self):
        """
        EnterpriseUserViewset should ultimately return a response that
        includes the enrollment_count field if "enrollment_count" is specified
        in the "extra_fields" query parameter value
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user4.id,
        }
        params = {'extra_fields': 'enrollment_count', }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['enrollment_count'] == 2

    def test_viewset_enrollment_count_not_present(self):
        """
        EnterpriseUserViewset should ultimately return a response that
        does not include the "enrollment_count" field if "enrollment_count"
        is not specified in the "extra_fields" query parameter value
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user4.id,
        }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url,)
        assert 'enrollment_count' not in response.json()

    def test_no_page_querystring_skips_pagination(self):
        """
        EnterpriseUserViewset list view should honor the no_page query param,
        returning results for in list, which is necessary for csv generation
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {'no_page': 'true', }

        response = self.client.get(url, params)


class TestEnterpriseLearnerCompletedCourses(APITestCase):
    """
    Tests for EnterpriseLearnerCompletedCoursesViewSet.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super(TestEnterpriseLearnerCompletedCourses, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        enterprise_api_client = mock.patch('enterprise_data.permissions.EnterpriseApiClient')
        self.enterprise_api_client = enterprise_api_client.start()
        self.addCleanup(enterprise_api_client.stop)

        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': self.enterprise_id
        }

    def test_get_learner_completed_courses(self):
        """
        Test that we get correct number of courses completed by a learner.
        """
        url = reverse('v0:enterprise-learner-completed-courses-list', kwargs={'enterprise_id': self.enterprise_id})
        expected_result = {
            'count': 1,
            'num_pages': 1,
            'current_page': 1,
            'results': [{
                'completed_courses': 2,
                'user_email': 'test@example.com'
            }],
            'next': None,
            'start': 0,
            'previous': None
        }
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result == expected_result

    def test_no_page_querystring_skips_pagination(self):
        """
        Test that when no_page is passed, pagination is skipped and we get expected response.
        """
        url = reverse('v0:enterprise-learner-completed-courses-list',
                      kwargs={'enterprise_id': self.enterprise_id})
        url += '?no_page=true'
        expected_result = [{'completed_courses': 2, 'user_email': 'test@example.com'}]
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # without pagination results are a list, not dict so we assert the data type and length
        assert isinstance(result, list)
        assert len(result) == 1
        assert result == expected_result
