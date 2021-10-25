"""
Tests for views in the `enterprise_data` module.
"""

from datetime import date, datetime, timedelta
from unittest import mock

import ddt
import pytz
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from django.utils import timezone

from enterprise_data.api.v0.serializers import EnterpriseEnrollmentSerializer
from enterprise_data.api.v0.views import subtract_one_month
from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import (
    EnterpriseEnrollmentFactory,
    EnterpriseUserFactory,
    UserFactory,
    get_dummy_enterprise_api_data,
)
from enterprise_data_roles.constants import (
    ALL_ACCESS_CONTEXT,
    ENTERPRISE_DATA_ADMIN_ROLE,
    SYSTEM_ENTERPRISE_ADMIN_ROLE,
    SYSTEM_ENTERPRISE_OPERATOR_ROLE,
)
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
@mark.django_db
class TestEnterpriseEnrollmentsViewSet(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseEnrollmentsViewSet
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

        mocked_get_enterprise_customer = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer',
            return_value=get_dummy_enterprise_api_data()
        )

        self.mocked_get_enterprise_customer = mocked_get_enterprise_customer.start()
        self.addCleanup(mocked_get_enterprise_customer.stop)
        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseUser.objects.all().delete()
        EnterpriseEnrollment.objects.all().delete()

    @staticmethod
    def _get_enrollments_expected_data(enrollments):
        """
        :param enrollments: List of enterprise Enrollments
        :return: expected response
        """
        return {
            'count': len(enrollments),
            'num_pages': 1,
            'current_page': 1,
            'results': [EnterpriseEnrollmentSerializer(enrollment).data for enrollment in enrollments],
            'next': None,
            'start': 0,
            'previous': None
        }

    def _assert_empty_result(self, response):
        """
        Checks the response has 200 status and empty list in results.
        """
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['count'] == 0
        assert result['results'] == []

    def test_get_queryset_returns_enrollments(self):
        enterprise_id = self.enterprise_id
        self.mocked_get_enterprise_customer.return_value = {
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
                'progress_status': 'Passed',
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
                'enterprise_id': self.enterprise_id,
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
                'progress_status': 'Failed',
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
                'enterprise_id': self.enterprise_id,
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

    def test_get_queryset_returns_no_enrollments(self):
        """ Test that enterprise with no enrollments returns empty list """
        enterprise = EnterpriseUserFactory()
        enterprise_id = enterprise.enterprise_id
        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id})

        response = self.client.get(url)
        self._assert_empty_result(response)

    def test_empty_result_for_invalid_enterprise_uuid(self):
        """ Test that a empty data is returned when there is no enterprise for the requested UUID """
        EnterpriseUserFactory()
        fake_enterprise_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': fake_enterprise_id})

        response = self.client.get(url)
        self._assert_empty_result(response)

    def test_get_queryset_returns_enrollments_with_passed_date_filter(self):
        enterprise = EnterpriseUserFactory()
        enterprise_id = enterprise.enterprise_id
        url = "{url}?passed_date=last_week".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id})
        )

        date_today = timezone.now()
        in_past_week_passed_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_passed_dates = [date_today - timedelta(weeks=2)]
        passed_dates = in_past_week_passed_dates + before_past_week_passed_dates
        for index, passed_date in enumerate(passed_dates):
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise,
                enterprise_id=enterprise_id,
                user_email=f'user{index}@example.com',
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
            assert enrollment['progress_status'] == 'Passed'
            assert enrollment['passed_timestamp'] == passed_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @ddt.data(
        (
            True, None, None, 2, 'verified', 2
        ),
        (
            True, None, None, 2, 'audit', 2
        ),
        (
            False, None, None, 2, 'verified', 2
        ),
        (
            False, None, None, 2, 'audit', 0
        ),
        (
            True, 'Test Coupon Code', None, 2, 'verified', 2
        ),
        (
            True, 'Test Coupon Code', None, 2, 'audit', 2
        ),
        (
            False, 'Test Coupon Code', None, 2, 'verified', 2
        ),
        (
            False, 'Test Coupon Code', None, 2, 'audit', 2
        ),
        (
            True, None, 'Test Offer', 2, 'verified', 2
        ),
        (
            True, None, 'Test Offer', 2, 'audit', 2
        ),
        (
            False, None, 'Test Offer', 2, 'verified', 2
        ),
        (
            False, None, 'Test Offer', 2, 'audit', 2
        ),
        (
            True, 'Test Coupon Code', 'Test Offer', 2, 'verified', 2
        ),
        (
            True, 'Test Coupon Code', 'Test Offer', 2, 'audit', 2
        ),
        (
            False, 'Test Coupon Code', 'Test Offer', 2, 'verified', 2
        ),
        (
            False, 'Test Coupon Code', 'Test Offer', 2, 'audit', 2
        ),
    )
    @ddt.unpack
    def test_get_queryset_returns_enrollments_with_audit_enrollment_filter(
            self, enable_audit_data_reporting, coupon_code, offer, total_enrollments,
            user_current_enrollment_mode, enrollments_count
    ):
        enterprise_user = EnterpriseUserFactory()
        enterprise_id = enterprise_user.enterprise_id
        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id})

        self.mocked_get_enterprise_customer.return_value = get_dummy_enterprise_api_data(
            enterprise_id=enterprise_id,
            enable_audit_data_reporting=enable_audit_data_reporting,
        )

        for index in range(total_enrollments):
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise_user,
                enterprise_id=enterprise_id,
                user_email=f'user{index}@example.com',
                user_current_enrollment_mode=user_current_enrollment_mode,
                course_title='course101',
                has_passed=True,
                consent_granted=True,
                coupon_name=f'Test Coupon {index}',
                coupon_code=coupon_code,
                offer=offer,
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

        enterprise = EnterpriseUserFactory()
        enterprise_id = enterprise.enterprise_id
        url = "{url}?learner_activity={activity_filter}".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id}),
            activity_filter=activity_filter
        )

        date_today = date.today()
        in_past_week_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_dates = [date_today - timedelta(weeks=2)]
        before_past_month_dates = [subtract_one_month(date.today())]
        activity_dates = in_past_week_dates + before_past_week_dates + before_past_month_dates
        start_date = timezone.now() - timedelta(days=60)
        end_date = timezone.now() + timedelta(days=1)

        for activity_date in activity_dates:
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise,
                enterprise_id=enterprise_id,
                last_activity_date=activity_date,
                course_start=start_date,
                course_end=end_date,
                has_passed=False
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
        enterprise = EnterpriseUserFactory()
        enterprise_id = enterprise.enterprise_id
        url = "{url}?learner_activity={activity_filter}".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id}),
            activity_filter=activity_filter
        )

        course_end_date = timezone.now() + timedelta(days=1)

        date_today = date.today()
        in_past_week_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_dates = [date_today - timedelta(weeks=2)]
        before_past_month_dates = [subtract_one_month(date.today())]
        activity_dates = in_past_week_dates + before_past_week_dates + before_past_month_dates
        for activity_date in activity_dates:
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise,
                enterprise_id=enterprise_id,
                last_activity_date=activity_date,
                course_end=course_end_date,
                has_passed=False,
                consent_granted=False,
            )

        response = self.client.get(url)
        self._assert_empty_result(response)

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
        enterprise = EnterpriseUserFactory()
        enterprise_id = enterprise.enterprise_id
        url = "{url}?learner_activity={activity_filter}".format(
            url=reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': enterprise_id}),
            activity_filter=activity_filter
        )

        date_today = date.today()
        in_past_week_dates = [date_today, date_today - timedelta(days=2)]
        before_past_week_dates = [date_today - timedelta(weeks=2)]
        before_past_month_dates = [subtract_one_month(date.today())]
        activity_dates = in_past_week_dates + before_past_week_dates + before_past_month_dates
        for activity_date in activity_dates:
            EnterpriseEnrollmentFactory(
                enterprise_user=enterprise,
                enterprise_id=enterprise_id,
                last_activity_date=activity_date,
                course_start=course_end_date - timedelta(days=60),
                course_end=course_end_date,
                has_passed=has_passed,
                consent_granted=True,
            )

        response = self.client.get(url)
        self._assert_empty_result(response)

    def test_empty_result_for_no_enterprise_user(self):
        enterprise_id = '0395b02f-6b29-42ed-9a41-45f3dff8349c'
        self.mocked_get_enterprise_customer.return_value = {
            'uuid': enterprise_id
        }
        url = reverse('v0:enterprise-enrollments-list',
                      kwargs={'enterprise_id': enterprise_id})
        response = self.client.get(url)
        self._assert_empty_result(response)

    def test_get_overview_returns_overview(self):
        enterprise_id = self.enterprise_id
        self.mocked_get_enterprise_customer.return_value = {
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
        self.mocked_get_enterprise_customer.return_value = {
            'uuid': self.enterprise_id,
            'enable_audit_data_reporting': True,
            'enforce_data_sharing_consent': True,
        }
        url = reverse('v0:enterprise-enrollments-list',
                      kwargs={'enterprise_id': self.enterprise_id})
        url += '?no_page=true'
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # without pagination results are a list, not dict so we assert the data type and length
        assert isinstance(result, list)
        assert len(result) == 2

    @ddt.data(
        {
            'implicit': False,
            'explicit': False,
            'jwt_enterprise_id': None,
            'context_enterprise_id': None,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': None,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': True,
            'context_enterprise_id': None,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': False,
            'context_enterprise_id': True,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': False,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        }
    )
    @ddt.unpack
    def test_permissions(
            self,
            implicit,
            explicit,
            jwt_enterprise_id,
            context_enterprise_id,
            status  # pylint: disable=redefined-outer-name
    ):
        """
        Test that role base permissions works as expected.
        """
        self.mocked_get_enterprise_customer.return_value = {
            'uuid': self.enterprise_id,
            'enable_audit_data_reporting': True,
            'enforce_data_sharing_consent': True,
        }

        if context_enterprise_id:
            self.role_assignment.enterprise_id = self.enterprise_id
            self.role_assignment.save()

        role_context = 'some_context'
        if jwt_enterprise_id:
            role_context = self.enterprise_id

        system_wide_role = SYSTEM_ENTERPRISE_ADMIN_ROLE
        if implicit is False:
            system_wide_role = 'role_with_no_mapped_permissions'

        self.set_jwt_cookie(system_wide_role=system_wide_role, context=role_context)

        if explicit is False:
            EnterpriseDataRoleAssignment.objects.all().delete()

        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        assert response.status_code == status

    def test_permissions_with_enterprise_openedx_operator(self):
        """
        Test that role base permissions works as expected with `enterprise_openedx_operator` role.
        """
        self.mocked_get_enterprise_customer.return_value = {
            'uuid': self.enterprise_id,
            'enable_audit_data_reporting': True,
            'enforce_data_sharing_consent': True,
        }

        self.set_jwt_cookie(system_wide_role=SYSTEM_ENTERPRISE_OPERATOR_ROLE, context=ALL_ACCESS_CONTEXT)

        url = reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK


@ddt.ddt
@mark.django_db
class TestEnterpriseUsersViewSet(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseUsersViewSet
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)
        mocked_get_enterprise_customer = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer',
            return_value=get_dummy_enterprise_api_data()
        )

        self.mocked_get_enterprise_customer = mocked_get_enterprise_customer.start()
        self.addCleanup(mocked_get_enterprise_customer.stop)

        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'

        one_day = timedelta(days=1)
        self.today = timezone.now()
        course_end_date_in_past = self.today - one_day
        course_end_date_in_future = self.today + one_day
        course_start_date = course_end_date_in_future - timedelta(days=60)

        # Users without enrollments
        EnterpriseUserFactory(
            enterprise_user_id=1,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseUserFactory(
            enterprise_user_id=2,
            enterprise_id=self.enterprise_id,
        )
        self.ent_user3 = EnterpriseUserFactory(
            enterprise_user_id=3,
            enterprise_id=self.enterprise_id,
        )
        # User with True & None for enrollment consent
        self.ent_user4 = EnterpriseUserFactory(
            enterprise_user_id=4,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            consent_granted=True,
            has_passed=True,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
            enterprise_id=self.enterprise_id,
            consent_granted=None,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
            consent_granted=True,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user4,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            consent_granted=True,
            has_passed=False,
            enterprise_id=self.enterprise_id,
        )
        # User with only True enrollment consent
        self.ent_user5 = EnterpriseUserFactory(
            enterprise_user_id=5,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user5,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
            consent_granted=True,
            enterprise_id=self.enterprise_id,
        )
        # User with only False enrollment consent
        self.ent_user6 = EnterpriseUserFactory(
            enterprise_user_id=6,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user6,
            consent_granted=False,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            enterprise_id=self.enterprise_id,
        )
        # User with True and False enrollment consent
        self.ent_user7 = EnterpriseUserFactory(
            enterprise_user_id=7,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=True,
            has_passed=True,
            enterprise_id=self.enterprise_id,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=False,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
            has_passed=False,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user7,
            consent_granted=False,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            has_passed=True,
            enterprise_id=self.enterprise_id,
        )

        # User with True & None for enrollment consent and course has ended
        self.ent_user8 = EnterpriseUserFactory(
            enterprise_user_id=8,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user8,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            has_passed=True,
            enterprise_id=self.enterprise_id,
            consent_granted=None,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user8,
            consent_granted=True,
            course_start=course_start_date,
            course_end=course_end_date_in_past,
            has_passed=True,
            enterprise_id=self.enterprise_id,
        )

        # User with a large number of enrollments of different kinds
        self.ent_user9 = EnterpriseUserFactory(
            enterprise_user_id=9,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            has_passed=True,
            consent_granted=False,
            enterprise_id=self.enterprise_id,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
        )
        for _ in range(2):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.ent_user9,
                has_passed=False,
                enterprise_id=self.enterprise_id,
                consent_granted=False,
                course_start=course_start_date,
                course_end=course_end_date_in_future,
            )
        for _ in range(3):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.ent_user9,
                consent_granted=True,
                has_passed=True,
                enterprise_id=self.enterprise_id,
                course_start=course_start_date,
                course_end=course_end_date_in_future,
            )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            consent_granted=False,
            has_passed=True,
            enterprise_id=self.enterprise_id,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user9,
            consent_granted=True,
            has_passed=False,
            enterprise_id=self.enterprise_id,
            course_start=course_start_date,
            course_end=course_end_date_in_future,
        )

        # User with a audit mode enrollment
        self.ent_user10 = EnterpriseUserFactory(
            enterprise_user_id=10,
            enterprise_id=self.enterprise_id,
        )
        EnterpriseEnrollmentFactory(
            enterprise_user=self.ent_user10,
            has_passed=True,
            enterprise_id=self.enterprise_id,
            consent_granted=True,
            user_current_enrollment_mode='audit',
            course_start=course_start_date,
            course_end=course_end_date_in_future,
        )
        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseUser.objects.all().delete()
        EnterpriseEnrollment.objects.all().delete()

    def test_viewset_no_query_params(self):
        """
        EnterpriseUserViewset should return all users if no filtering query
        params are present
        """
        url = reverse('v0:enterprise-users-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)
        assert response.json()['count'] == 8

    def test_viewset_with_audit_reporting(self):
        """
        EnterpriseUserViewset should return all users inclusive with audit enrollments.
        """
        self.mocked_get_enterprise_customer.return_value = {
            'uuid': self.enterprise_id,
            'enable_audit_data_reporting': True,
        }
        url = reverse('v0:enterprise-users-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)
        assert response.json()['count'] == 9

    @mock.patch('enterprise_data.api.v0.views.EnterpriseUsersViewSet.paginate_queryset')
    def test_viewset_no_query_params_no_pagination(self, mock_paginate):
        """
        EnterpriseUserViewset should return all users if no filtering query
        params are present in a list if no pagination occurs
        """
        mock_paginate.return_value = None
        url = reverse('v0:enterprise-users-list',
                      kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)
        assert 'count' not in response.json()
        assert len(response.json()) == 8

    def test_viewset_filter_has_enrollments_true(self):
        """
        EnterpriseUserViewset should return all users that have enrollments
        if query param value is 'true'
        """
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
        params = {'active_courses': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )

        response = self.client.get(url, params)
        assert response.json()['count'] == 4

    def test_viewset_filter_active_courses_false(self):
        """
        EnterpriseUserViewset should filter out enrollments for courses that
        have a course_end date in the future if active_courses query param
        value is false
        """
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
            'enterprise_id': self.enterprise_id,
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
            'enterprise_id': self.enterprise_id,
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
            'enterprise_id': self.enterprise_id,
            'pk': self.ent_user4.id,
        }
        params = {'extra_fields': ['enrollment_count', 'course_completion_count'], }
        url = reverse(
            'v0:enterprise-users-detail',
            kwargs=kwargs,
        )
        response = self.client.get(url, params)
        # There will be a KeyError if the key is not present
        assert response.json()['enrollment_count']
        assert response.json()['course_completion_count']

    def test_viewset_enrollment_count_consent(self):
        """
        EnterpriseUserViewset should respect consent_granted on enrollments
        when determining the enrollment_count for a user
        """
        kwargs = {
            'enterprise_id': self.enterprise_id,
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
            'enterprise_id': self.enterprise_id,
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
            'enterprise_id': self.enterprise_id,
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
        kwargs = {'enterprise_id': self.enterprise_id, }
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
            'enterprise_id': self.enterprise_id,
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
        kwargs = {'enterprise_id': self.enterprise_id, }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )
        params = {'no_page': 'true', }

        response = self.client.get(url, params)
        assert isinstance(response.json(), list)
        assert len(response.json()) == 8

    @ddt.data('id', '-id')
    def test_viewset_ordering(self, ordering):
        """
        EnterpriseUserViewset should order users returned if the value
        for ordering query param is set
        """
        order = {
            'id': False,
            '-id': True,
        }

        kwargs = {'enterprise_id': self.enterprise_id, }
        params = {'ordering': ordering, 'has_enrollments': 'true', }
        url = reverse(
            'v0:enterprise-users-list',
            kwargs=kwargs,
        )

        response = self.client.get(url, params)
        assert response.json()['count'] == 5
        response = response.json()
        result_ids = [result['id'] for result in response['results']]

        assert result_ids == sorted(result_ids, reverse=order[ordering])

    @ddt.data(
        {
            'implicit': False,
            'explicit': False,
            'jwt_enterprise_id': None,
            'context_enterprise_id': None,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': None,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': True,
            'context_enterprise_id': None,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': False,
            'context_enterprise_id': True,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': False,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        }
    )
    @ddt.unpack
    def test_permissions(
            self,
            implicit,
            explicit,
            jwt_enterprise_id,
            context_enterprise_id,
            status  # pylint: disable=redefined-outer-name
    ):
        """
        Test that role base permissions works as expected.
        """
        if context_enterprise_id:
            self.role_assignment.enterprise_id = self.enterprise_id
            self.role_assignment.save()

        role_context = 'some_context'
        if jwt_enterprise_id:
            role_context = self.enterprise_id

        system_wide_role = SYSTEM_ENTERPRISE_ADMIN_ROLE
        if implicit is False:
            system_wide_role = 'role_with_no_mapped_permissions'

        self.set_jwt_cookie(system_wide_role=system_wide_role, context=role_context)

        if explicit is False:
            EnterpriseDataRoleAssignment.objects.all().delete()

        url = reverse('v0:enterprise-users-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, {'has_enrollments': 'true'})

        assert response.status_code == status

    def test_permissions_with_enterprise_openedx_operator(self):
        """
        Test that role base permissions works as expected with `enterprise_openedx_operator` role.
        """
        self.set_jwt_cookie(system_wide_role=SYSTEM_ENTERPRISE_OPERATOR_ROLE, context=ALL_ACCESS_CONTEXT)

        url = reverse('v0:enterprise-users-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK


@ddt.ddt
class TestEnterpriseLearnerCompletedCourses(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseLearnerCompletedCoursesViewSet.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)
        enterprise_api_client = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient',
            mock.Mock(
                return_value=mock.Mock(
                    get_enterprise_customer=mock.Mock(return_value=get_dummy_enterprise_api_data())
                )
            )
        )
        self.enterprise_api_client = enterprise_api_client.start()
        self.addCleanup(enterprise_api_client.stop)

        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise_api_client.return_value.get_enterprise_customer.return_value = {
            'uuid': self.enterprise_id
        }

        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseUser.objects.all().delete()
        EnterpriseEnrollment.objects.all().delete()

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
        course_start = date_in_past - timedelta(days=60)
        ent_user = EnterpriseUserFactory(enterprise_id=self.enterprise_id)
        for enrollment in enrollments_data:
            for _idx in range(enrollment['user_enrollments']):
                EnterpriseEnrollmentFactory(
                    user_email=enrollment['user_email'],
                    enterprise_user=ent_user,
                    enterprise_id=self.enterprise_id,
                    course_end=date_in_past,
                    course_start=course_start,
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

    @ddt.data(
        {
            'implicit': False,
            'explicit': False,
            'jwt_enterprise_id': None,
            'context_enterprise_id': None,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': None,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': True,
            'context_enterprise_id': None,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': True,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': False,
            'explicit': True,
            'jwt_enterprise_id': True,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        },
        {
            'implicit': True,
            'explicit': False,
            'jwt_enterprise_id': False,
            'context_enterprise_id': True,
            'status': status.HTTP_403_FORBIDDEN
        },
        {
            'implicit': True,
            'explicit': True,
            'jwt_enterprise_id': False,
            'context_enterprise_id': False,
            'status': status.HTTP_200_OK
        }
    )
    @ddt.unpack
    def test_permissions(
            self,
            implicit,
            explicit,
            jwt_enterprise_id,
            context_enterprise_id,
            status  # pylint: disable=redefined-outer-name
    ):
        """
        Test that role base permissions works as expected.
        """
        if context_enterprise_id:
            self.role_assignment.enterprise_id = self.enterprise_id
            self.role_assignment.save()

        role_context = 'some_context'
        if jwt_enterprise_id:
            role_context = self.enterprise_id

        system_wide_role = SYSTEM_ENTERPRISE_ADMIN_ROLE
        if implicit is False:
            system_wide_role = 'role_with_no_mapped_permissions'

        self.set_jwt_cookie(system_wide_role=system_wide_role, context=role_context)

        if explicit is False:
            EnterpriseDataRoleAssignment.objects.all().delete()

        url = reverse('v0:enterprise-learner-completed-courses-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        assert response.status_code == status

    def test_permissions_with_enterprise_openedx_operator(self):
        """
        Test that role base permissions works as expected with `enterprise_openedx_operator` role.
        """
        self.set_jwt_cookie(system_wide_role=SYSTEM_ENTERPRISE_OPERATOR_ROLE, context=ALL_ACCESS_CONTEXT)

        url = reverse('v0:enterprise-learner-completed-courses-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK


@ddt.ddt
@mark.django_db
class TestEnterpriseEnrollmentsViewSetFilters(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseEnrollmentsViewSet
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

        mocked_get_enterprise_customer = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer',
            return_value=get_dummy_enterprise_api_data()
        )

        self.mocked_get_enterprise_customer = mocked_get_enterprise_customer.start()
        self.addCleanup(mocked_get_enterprise_customer.stop)
        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

        self.email_0 = "robot@robot.com"
        self.email_1 = "mrrobot@foo.com"
        self.email_2 = "definitelyHuman@bar.com"
        self.enterprise_user_0 = EnterpriseUserFactory(enterprise_id=self.enterprise_id, user_email=self.email_0)
        self.enterprise_user_1 = EnterpriseUserFactory(enterprise_id=self.enterprise_id, user_email=self.email_1)
        self.enterprise_user_2 = EnterpriseUserFactory(enterprise_id=self.enterprise_id, user_email=self.email_2)

        self.course_title_0 = "Beekeeping 101"
        self.course_title_1 = "Keeping it together"
        self.course_title_2 = "Plan 101"

        self.course_date_0 = pytz.utc.localize(datetime(2020, 9, 30))
        self.course_date_1 = pytz.utc.localize(datetime(2020, 9, 3))
        self.course_date_2 = pytz.utc.localize(datetime(2020, 8, 30))

        self.all_course_titles = [self.course_title_0, self.course_title_1, self.course_title_2]
        self.all_course_dates = [self.course_date_0, self.course_date_1, self.course_date_2]
        self.all_emails = [self.email_0, self.email_1, self.email_2]

        # User 1 is enrolled in each course title with it's corresponding course date
        for course_date, title in zip(self.all_course_dates, self.all_course_titles):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.enterprise_user_0,
                enterprise_id=self.enterprise_id,
                user_email=self.enterprise_user_0.user_email,
                consent_granted=True,
                course_title=title,
                course_start=course_date,
            )

        # User 2 is enrolled in the same first two courses and titles as user1
        for course_date, title in zip(
                                      [self.course_date_0, self.course_date_1],
                                      [self.course_title_0, self.course_title_1]):
            EnterpriseEnrollmentFactory(
                enterprise_user=self.enterprise_user_1,
                enterprise_id=self.enterprise_id,
                user_email=self.enterprise_user_1.user_email,
                consent_granted=True,
                course_title=title,
                course_start=course_date,
            )

        # User 3 is enrolled in the first course, but a different course run (different date)
        EnterpriseEnrollmentFactory(
                enterprise_user=self.enterprise_user_2,
                enterprise_id=self.enterprise_id,
                user_email=self.enterprise_user_2.user_email,
                consent_granted=True,
                course_title=self.course_title_0,
                course_start=self.course_date_1,
            )

    def tearDown(self):
        super().tearDown()
        EnterpriseUser.objects.all().delete()
        EnterpriseEnrollment.objects.all().delete()

    @ddt.data(
        ("robot@robot.com", 3),  # the user with this email has 3 enrollements
        ('robot', 5),  # Two users have 'robot' in their emails, between them there are 5 enrollments
        ('human', 1),  # The user with 'human' in their email has only one enrollment
        ('test_5678@example.com', 0),  # there is no user with this email
    )
    @ddt.unpack
    def test_get_enterprise_enrollments_with_email_search(self, search_email, expected_count):
        """Test that with email_search param we get correct results"""

        expected_emails = [email for email in self.all_emails if search_email.lower() in email.lower()]
        response = self.client.get(
            reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id}),
            data={'search': search_email}
        ).json()

        assert response['count'] == expected_count
        for result in response['results']:
            assert result['user_email'] in expected_emails

    @ddt.data(
        ('keep', 5),  # there are 5 enrollments in the that have 'keep' in their title
        ('Beekeep', 3),  # there are only 3 enrollments with 'Beekeep' in their title
        ('plan', 1)  # there is only one enrollment with 'plan' in the title
    )
    @ddt.unpack
    def test_get_enterprise_enrollments_with_course_search(self, search_course, expected_count):
        expected_titles = [title for title in self.all_course_titles if search_course.lower() in title.lower()]
        response = self.client.get(
            reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id}),
            data={'search_course': search_course}
        ).json()
        response = self.client.get(
            reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id}),
            data={'search_course': search_course}
        ).json()

        assert response['count'] == expected_count

        for result in response["results"]:
            assert result["course_title"] in expected_titles

    # the expected_count corresponds to the number of enrollments that have that start date
    @ddt.data(
        ('2020-09-30T00:00:00Z', 2),
        ('2020-09-03T00:00:00Z', 3),
        ('2020-08-30T00:00:00Z', 1)
    )
    @ddt.unpack
    def test_get_enterprise_enrollments_with_start_date_search(self, search_date, expected_count):
        response = self.client.get(
            reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id}),
            data={'search_start_date': search_date}
        ).json()

        assert response['count'] == expected_count

        for result in response["results"]:
            assert result["course_start"] == search_date

    @ddt.data(
        ("", "keep", "2020-09-03T00:00:00Z", 3),  # of the 5 courses with keep in the name, 3 start on this date
        ("robot", "", "2020-09-03T00:00:00Z", 2),  # 2 users have 'robot' emails who have enrollments on this date
        ("robot", "Beekeep", "", 2),  # 2 users have the 'robot' email, each is enrolled in a Beekeeping course
        ("robot@robot.com", "keep", "2020-09-03T00:00:00Z", 1),  # there is only one enrollment that matches
        ("mrrobot@foo.com", "Plan", "", 0)  # user email exists, but the user has no courses with plan in the title
    )
    @ddt.unpack
    def test_get_enrollments_multiple_filters(self, search_email, search_course, search_date, expected_count):
        """ Integration test ensuring that filters work together as expected """

        expected_titles = [title for title in self.all_course_titles if search_course.lower() in title.lower()]
        expected_emails = [email for email in self.all_emails if search_email.lower() in email.lower()]
        data_dict = {}
        if search_date:
            data_dict["search_start_date"] = search_date
        if search_course:
            data_dict["search_course"] = search_course
        if search_email:
            data_dict["search"] = search_email

        response = self.client.get(
            reverse('v0:enterprise-enrollments-list', kwargs={'enterprise_id': self.enterprise_id}),
            data=data_dict
        ).json()

        assert response['count'] == expected_count

        for result in response["results"]:
            if search_date:
                assert result["course_start"] == search_date
            if search_course:
                assert result["course_title"] in expected_titles
            if search_email:
                assert result["user_email"] in expected_emails
