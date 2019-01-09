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
from enterprise_data.tests.test_utils import (
    EnterpriseEnrollmentFactory,
    EnterpriseUserFactory,
    UserFactory,
    get_dummy_enterprise_api_data,
)


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
        self.client.force_authenticate(user=self.user)  # pylint: disable=no-member
        enterprise_api_client = mock.patch(
            'enterprise_data.permissions.EnterpriseApiClient',
            mock.Mock(
                return_value=mock.Mock(
                    get_with_access_to=mock.Mock(return_value=get_dummy_enterprise_api_data())
                )
            )
        )
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
                'unenrollment_timestamp': '2014-06-29T16:02:38Z',
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
                'unenrollment_end_within_date': True,
            }, {
                'enrollment_created_timestamp': '2014-06-27T16:02:38Z',
                'unenrollment_timestamp': '2016-09-05T16:02:38Z',
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
                'unenrollment_end_within_date': True,
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
            True, 2, 'verified', 2
        ),
        (
            True, 2, 'audit', 2
        ),
        (
            False, 2, 'verified', 2
        ),
        (
            False, 2, 'audit', 0
        ),
    )
    @ddt.unpack
    def test_get_queryset_returns_enrollments_with_audit_enrollment_filter(
            self, enable_audit_enrollment, total_enrollments, user_current_enrollment_mode, enrollments_count
    ):
        enterprise_id = '413a0720-3efe-4cf5-98c8-3b4e42d3c501'
        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id})

        dummy_enterprise_api_data = get_dummy_enterprise_api_data(
            enterprise_id=enterprise_id,
            enable_audit_enrollment=enable_audit_enrollment,
        )
        enterprise_api_client = mock.patch(
            'enterprise_data.permissions.EnterpriseApiClient',
            mock.Mock(
                return_value=mock.Mock(
                    get_with_access_to=mock.Mock(return_value=dummy_enterprise_api_data)
                )
            )
        )
        self.enterprise_api_client = enterprise_api_client.start()
        enterprise_user = EnterpriseUserFactory(enterprise_user_id=1234)
        for index in range(total_enrollments):
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise_user,
                enterprise_id=enterprise_id,
                user_email='user{}@example.com'.format(index),
                user_current_enrollment_mode=user_current_enrollment_mode,
                course_title='course101',
                has_passed=True,
                consent_granted=True,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == enrollments_count

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
                course_end=timezone.now() + timedelta(days=1),
                has_passed=False,
                consent_granted=True,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == len(expected_dates)
        for enrollment in result['results']:
            assert datetime.strptime(enrollment['last_activity_date'], "%Y-%m-%d").date() in expected_dates

    @ddt.data(
        (
            'active_past_week',
        ),
        (
            'inactive_past_week',
        ),
        (
            'inactive_past_month',
        )
    )
    @ddt.unpack
    def test_get_queryset_returns_learner_activity_filter_no_consent(self, activity_filter):
        """
        Learner activity filter should not return learner if their enrollments
        have no consent granted
        """
        enterprise_id = '413a0720-3efe-4cf5-98c8-3b4e42d3c509'
        url = u"{url}?learner_activity={activity_filter}".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id}),
            activity_filter=activity_filter
        )

        enterprise_user = EnterpriseUserFactory(enterprise_user_id=1234)
        course_end_date = timezone.now() + timedelta(days=1)

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
                course_end=course_end_date,
                has_passed=False,
                consent_granted=False,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == 0

    @ddt.data(
        # passed, course date in past
        (
            'active_past_week',
            True,
            timezone.now() + timedelta(days=-1),
        ),
        (
            'inactive_past_week',
            True,
            timezone.now() + timedelta(days=-1),
        ),
        (
            'inactive_past_month',
            True,
            timezone.now() + timedelta(days=-1),
        ),
        # passed, course date in future
        (
            'active_past_week',
            True,
            timezone.now() + timedelta(days=1),
        ),
        (
            'inactive_past_week',
            True,
            timezone.now() + timedelta(days=1),
        ),
        (
            'inactive_past_month',
            True,
            timezone.now() + timedelta(days=1),
        ),
        # not passed, course date in past
        (
            'active_past_week',
            False,
            timezone.now() + timedelta(days=-1),
        ),
        (
            'inactive_past_week',
            False,
            timezone.now() + timedelta(days=-1),
        ),
        (
            'inactive_past_month',
            False,
            timezone.now() + timedelta(days=-1),
        ),
    )
    @ddt.unpack
    def test_get_queryset_returns_learner_activity_filter_no_active_enrollments(
            self, activity_filter, has_passed, course_end_date
    ):
        """
        Learner activity filter should not return enrollments if their course date is in past
        or learners have not passed the course yet.
        """
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
                course_end=course_end_date,
                has_passed=has_passed,
                consent_granted=True,
            )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

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


@ddt.ddt
@mark.django_db
class TestEnterpriseUsersViewSet(APITestCase):
    """
    Tests for EnterpriseUsersViewSet
    """

    def setUp(self):
        super(TestEnterpriseUsersViewSet, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)  # pylint: disable=no-member
        enterprise_api_client = mock.patch(
            'enterprise_data.permissions.EnterpriseApiClient',
            mock.Mock(
                return_value=mock.Mock(
                    get_with_access_to=mock.Mock(return_value=get_dummy_enterprise_api_data())
                )
            )
        )
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
        self.ent_user3 = EnterpriseUserFactory(
            enterprise_user_id=3,
        )
        # User with True & None for enrollment consent
        self.ent_user4 = EnterpriseUserFactory(
            enterprise_user_id=4,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_past,
            consent_granted=True,
            has_passed=True,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_future,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_future,
            consent_granted=True,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_end=date_in_past,
            consent_granted=True,
            has_passed=False,
        )
        # User with only True enrollment consent
        self.ent_user5 = EnterpriseUserFactory(
            enterprise_user_id=5,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user5,
            course_end=date_in_future,
            consent_granted=True,
        )
        # User with only False enrollment consent
        self.ent_user6 = EnterpriseUserFactory(
            enterprise_user_id=6,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user6,
            consent_granted=False,
            course_end=date_in_past,
        )
        # User with True and False enrollment consent
        self.ent_user7 = EnterpriseUserFactory(
            enterprise_user_id=7,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=True,
            has_passed=True,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=False,
            course_end=date_in_future,
            has_passed=False,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=False,
            course_end=date_in_past,
            has_passed=True,
        )

        # User with True & None for enrollment consent and course has ended
        self.ent_user8 = EnterpriseUserFactory(
            enterprise_user_id=8,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user8,
            course_end=date_in_past,
            has_passed=True,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user8,
            consent_granted=True,
            course_end=date_in_past,
            has_passed=True,
        )

        # User with a large number of enrollments of different kinds
        self.ent_user9 = EnterpriseUserFactory(
            enterprise_user_id=9,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            has_passed=True,
        )
        for _ in range(2):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.ent_user9,
                has_passed=False,
            )
        for _ in range(3):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.ent_user9,
                consent_granted=True,
                has_passed=True,
            )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            consent_granted=False,
            has_passed=True,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            consent_granted=True,
            has_passed=False,
        )

    def test_viewset_no_query_params(self):
        """
        EnterpriseUserViewset should return all users if no filtering query
        params are present
        """
        url = reverse('v0:enterprise-users-list',
                      kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})
        response = self.client.get(url)
        assert response.json()['count'] == 8

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
        assert len(response.json()) == 8

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
        assert response.json()['count'] == 5

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
        assert response.json()['count'] == 8

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
        assert response.json()['count'] == 2

    def test_viewset_filter_all_enrollments_passed_true(self):
        """
        EnterpriseUserViewset should return all those users that have all
        enrollments with passed status and also those enrollments are only for
        those courses which have `course_end` date in the past, if
        `has_enrollments` query param is true, `active_courses` query param is
        false and `all_enrollments_passed` query param is true.
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'has_enrollments': 'true', 'active_courses': 'false', 'all_enrollments_passed': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 1

    def test_viewset_filter_all_enrollments_passed_false(self):
        """
        EnterpriseUserViewset should return all those users that have all
        enrollments with failed status and also those enrollments are only for
        those courses which have `course_end` date in the past, if
        `has_enrollments` query param is true, `active_courses` query param is
        false and `all_enrollments_passed` query param is false.
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'has_enrollments': 'true', 'active_courses': 'false', 'all_enrollments_passed': 'false', }
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
        params = {'extra_fields': ['enrollment_count'], }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['enrollment_count'] == 3

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

    def test_viewset_enrollment_count_and_course_completion_count_present(self):
        """
        EnterpriseUserViewset should ultimately return a response that includes
        both the `enrollment_count` field and `course_completion_count` field
        if value ["enrollment_count", "course_completion_count"] is specified in
        the `extra_fields` query parameter value.
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user4.id,
        }
        params = {'extra_fields': ['enrollment_count', 'course_completion_count'], }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['enrollment_count'] == 3
        assert response.json()['course_completion_count'] == 1

    def test_viewset_enrollment_count_consent(self):
        """
        EnterpriseUserViewset should respect consent_granted on enrollments
        when determining the enrollment_count for a user
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user7.id,
        }
        params = {'extra_fields': ['enrollment_count'], }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['enrollment_count'] == 1

    def test_viewset_course_completion_count_not_present(self):
        """
        EnterpriseUserViewset should ultimately return a response that
        does not include the `course_completion_count` field if
        "course_completion_count" is not specified in the "extra_fields" query
        parameter value.
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
        assert 'course_completion_count' not in response.json()

    def test_viewset_course_completion_consent(self):
        """
        EnterpriseUserViewset should respect consent_granted on enrollments
        when determining the course_completion_count for a user
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user7.id,
        }
        params = {'extra_fields': ['course_completion_count'], }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['course_completion_count'] == 1

    def test_users_are_sortable_by_enrollment_count(self):
        """
        EnterpriseUserViewset list view should be able to return a list
        of users sorted by their respective enrollment counts
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {
            'extra_fields': 'enrollment_count',
            'ordering': 'enrollment_count'
        }
        response = self.client.get(url, params)
        current_enrollment_count = 0
        for user in response.json()['results']:
            assert user['enrollment_count'] >= current_enrollment_count
            current_enrollment_count = user['enrollment_count']

    def test_users_are_sortable_by_enrollment_count_reverse(self):
        """
        EnterpriseUserViewset list view should be able to return a list
        of users reverse sorted by their respective enrollment counts
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {
            'extra_fields': 'enrollment_count',
            'ordering': '-enrollment_count'
        }
        response = self.client.get(url, params)
        current_enrollment_count = 99
        for user in response.json()['results']:
            assert user['enrollment_count'] <= current_enrollment_count
            current_enrollment_count = user['enrollment_count']

    def test_users_are_sortable_by_course_completion_count(self):
        """
        EnterpriseUserViewset list view should be able to return a list
        of users sorted by their respective course_completion_count
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {
            'extra_fields': 'course_completion_count',
            'ordering': 'course_completion_count'
        }
        response = self.client.get(url, params)
        current_course_completion_count = 0
        for user in response.json()['results']:
            assert user['course_completion_count'] >= current_course_completion_count
            current_course_completion_count = user['course_completion_count']

    def test_users_are_sortable_by_course_completion_count_reverse(self):
        """
        EnterpriseUserViewset list view should be able to return a list
        of users sorted by their respective course_completion_count
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {
            'extra_fields': 'course_completion_count',
            'ordering': '-course_completion_count'
        }
        response = self.client.get(url, params)
        current_course_completion_count = 99
        for user in response.json()['results']:
            assert user['course_completion_count'] <= current_course_completion_count
            current_course_completion_count = user['course_completion_count']

    def test_viewset_course_completion_count_value_regression(self):
        """
        EnterpriseUserViewset should return the correct value for course_completion_count
        instead of returning "1" when 1 or more completed (and consented) enrollments
        exist for a user.
        """
        kwargs = {
            'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            'pk': self.ent_user9.id,
        }
        params = {
            'extra_fields': ['enrollment_count', 'course_completion_count'],
            'ordering': 'course_completion_count',
        }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['enrollment_count'] == 4
        assert response.json()['course_completion_count'] == 3

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
        assert isinstance(response.json(), list)
        assert len(response.json()) == 8

    @ddt.data(
        (
            'id',
            [4, 9]
        ),
        (
            '-id',
            [9, 4]
        )
    )
    @ddt.unpack
    def test_viewset_ordering(self, ordering, users):
        """
        EnterpriseUserViewset should order users returned if the value
        for ordering query param is set
        """
        kwargs = {'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c', }
        params = {'ordering': ordering, 'has_enrollments': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        assert response.json()['count'] == 5
        assert response.json()['results'][0]['id'] == users[0]
        assert response.json()['results'][4]['id'] == users[1]


@ddt.ddt
class TestEnterpriseLearnerCompletedCourses(APITestCase):
    """
    Tests for EnterpriseLearnerCompletedCoursesViewSet.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super(TestEnterpriseLearnerCompletedCourses, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)  # pylint: disable=no-member
        enterprise_api_client = mock.patch(
            'enterprise_data.permissions.EnterpriseApiClient',
            mock.Mock(
                return_value=mock.Mock(
                    get_with_access_to=mock.Mock(return_value=get_dummy_enterprise_api_data())
                )
            )
        )
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
                'completed_courses': 1,
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
        expected_result = [{'completed_courses': 1, 'user_email': 'test@example.com'}]
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # without pagination results are a list, not dict so we assert the data type and length
        assert isinstance(result, list)
        assert len(result) == 1
        assert result == expected_result

    @ddt.data(
        (
            'completed_courses',
            [
                {
                    'user_email': 'test2@example.com',
                    'user_enrollments': 2,
                },
                {
                    'user_email': 'test3@example.com',
                    'user_enrollments': 3,
                },
            ],
            3,
            [1, 2, 3]
        ),
        (
            'completed_courses',
            [
                {
                    'user_email': 'test2@example.com',
                    'user_enrollments': 2,
                },
                {
                    'user_email': 'test3@example.com',
                    'user_enrollments': 3,
                },
                {
                    'user_email': 'test4@example.com',
                    'user_enrollments': 1,
                },
            ],
            4,
            [1, 1, 2, 3]
        ),
        (
            '-completed_courses',
            [
                {
                    'user_email': 'test2@example.com',
                    'user_enrollments': 2,
                },
                {
                    'user_email': 'test3@example.com',
                    'user_enrollments': 3,
                },
            ],
            3,
            [3, 2, 1]
        ),
        (
            '-completed_courses',
            [
                {
                    'user_email': 'test2@example.com',
                    'user_enrollments': 2,
                },
                {
                    'user_email': 'test3@example.com',
                    'user_enrollments': 3,
                },
                {
                    'user_email': 'test4@example.com',
                    'user_enrollments': 2,
                },
            ],
            4,
            [3, 2, 2, 1]
        ),
    )
    @ddt.unpack
    def test_viewset_ordering(
            self,
            ordering,
            enrollments_data,
            expected_results_count,
            expected_completed_courses
    ):
        """
        EnterpriseLearnerCompletedCoursesViewSet should order enrollments returned if the value
        for ordering query param is set.
        """
        # Add enrollments
        one_day = timedelta(days=1)
        date_in_past = timezone.now() - one_day
        ent_user = EnterpriseUserFactory(
            enterprise_user_id=1,
        )
        for enrollment in enrollments_data:
            for _idx in range(enrollment['user_enrollments']):
                EnterpriseEnrollmentFactory(
                    user_email=enrollment['user_email'],
                    enterprise_user=ent_user,
                    course_end=date_in_past,
                    has_passed=True,
                    consent_granted=True,
                )
        url = reverse(
            'v0:enterprise-learner-completed-courses-list',
            kwargs={'enterprise_id': self.enterprise_id}
        )
        params = {'ordering': ordering}
        response = self.client.get(url, params)
        assert response.json()['count'] == expected_results_count

        for idx, expected_course_completed_count in enumerate(expected_completed_courses):
            assert response.json()['results'][idx]['completed_courses'] == expected_course_completed_count
