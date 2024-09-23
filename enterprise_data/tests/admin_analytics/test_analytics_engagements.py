"""Unittests for analytics_enrollments.py"""

from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.tests.admin_analytics.mock_analytics_data import ENGAGEMENTS
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
class TestIndividualEngagementsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for AdvanceAnalyticsIndividualEngagementsView."""

    def setUp(self):
        """
        Setup method.
        """
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(
            name=ENTERPRISE_DATA_ADMIN_ROLE
        )
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role, user=self.user
        )
        self.client.force_authenticate(user=self.user)

        self.enterprise_uuid = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

        self.url = reverse(
            'v1:enterprise-admin-analytics-engagements',
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    @patch('enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_engagement_count')
    @patch('enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_all_engagements')
    def test_get(self, mock_get_all_engagements, mock_get_engagement_count):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEngagementsView works.
        """
        mock_get_all_engagements.return_value = ENGAGEMENTS
        mock_get_engagement_count.return_value = len(ENGAGEMENTS)

        response = self.client.get(self.url + '?page_size=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] == f"http://testserver{self.url}?page=2&page_size=2"
        assert data['previous'] is None
        assert data['current_page'] == 1
        assert data['num_pages'] == 6
        assert data['count'] == 12

        response = self.client.get(self.url + '?page_size=2&page=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] == f"http://testserver{self.url}?page=3&page_size=2"
        assert data['previous'] == f"http://testserver{self.url}?page_size=2"
        assert data['current_page'] == 2
        assert data['num_pages'] == 6
        assert data['count'] == 12

        response = self.client.get(self.url + '?page_size=2&page=6')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] is None
        assert data['previous'] == f"http://testserver{self.url}?page=5&page_size=2"
        assert data['current_page'] == 6
        assert data['num_pages'] == 6
        assert data['count'] == 12

        response = self.client.get(self.url + '?page_size=12')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] is None
        assert data['previous'] is None
        assert data['current_page'] == 1
        assert data['num_pages'] == 1
        assert data['count'] == 12

    @patch('enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_engagement_count')
    @patch('enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_all_engagements')
    def test_get_csv(self, mock_get_all_engagements, mock_get_engagement_count):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEngagementsView return correct CSV data.
        """
        mock_get_all_engagements.return_value = ENGAGEMENTS[0:4]
        mock_get_engagement_count.return_value = 4

        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response["Content-Type"] == "text/csv"

        # verify the response content
        content = b"".join(response.streaming_content).decode().splitlines()
        assert len(content) == 5

        # Verify CSV header.
        assert 'email,course_title,course_subject,enroll_type,activity_date,learning_time_hours' == content[0]

        # verify the content
        assert (
                'padillamichelle@example.org,Synergized reciprocal encoding,business-management,certificate,2021-08-05,'
                '1.0344444444444445'
                in content
        )
        assert (
                'yallison@example.org,Synergized reciprocal encoding,business-management,certificate,2021-07-27,'
                '1.2041666666666666'
                in content
        )
        assert (
                'weaverpatricia@example.net,Synergized reciprocal encoding,business-management,certificate,2021-08-05,'
                '2.6225'
                in content
        )
        assert (
                'seth57@example.org,Synergized reciprocal encoding,business-management,certificate,2021-08-21,'
                '2.7494444444444444'
                in content
        )

    @ddt.data(
        {
            'params': {'start_date': 1},
            'error': {
                'start_date': [
                    'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'
                ]
            },
        },
        {
            'params': {'end_date': 2},
            'error': {
                'end_date': [
                    'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'
                ]
            },
        },
        {
            'params': {"start_date": "2024-01-01", "end_date": "2023-01-01"},
            'error': {
                'non_field_errors': [
                    'start_date should be less than or equal to end_date.'
                ]
            },
        },
    )
    @ddt.unpack
    def test_get_invalid_query_params(self, params, error):
        """
        Test the GET method return correct error if any query param value is incorrect.
        """
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error


@ddt.ddt
class TestEngagementStatsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for AdvanceAnalyticsEngagementStatsView."""

    def setUp(self):
        """
        Setup method.
        """
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(
            name=ENTERPRISE_DATA_ADMIN_ROLE
        )
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role, user=self.user
        )
        self.client.force_authenticate(user=self.user)

        self.enterprise_uuid = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

        self.url = reverse(
            'v1:enterprise-admin-analytics-engagements-stats',
            kwargs={'enterprise_uuid': self.enterprise_uuid},
        )

        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    @patch(
        'enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.'
        'get_engagement_time_series_data'
    )
    @patch(
        'enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_top_courses_by_engagement'
    )
    @patch(
        'enterprise_data.api.v1.views.analytics_engagements.FactEngagementAdminDashTable.get_top_subjects_by_engagement'
    )
    def test_get(self, mock_get_top_subjects_by_engagement, mock_get_top_courses_by_engagement, mock_get_time_series):
        """
        Test the GET method for the AdvanceAnalyticsEnrollmentStatsView works.
        """
        mock_get_top_subjects_by_engagement.return_value = []
        mock_get_top_courses_by_engagement.return_value = []
        mock_get_time_series.return_value = []

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'engagement_over_time' in data
        assert 'top_courses_by_engagement' in data
        assert 'top_subjects_by_engagement' in data

    @ddt.data(
        {
            'params': {'start_date': 1},
            'error': {
                'start_date': [
                    'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'
                ]
            },
        },
        {
            'params': {'end_date': 2},
            'error': {
                'end_date': [
                    'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'
                ]
            },
        },
        {
            'params': {'start_date': '2024-01-01', 'end_date': '2023-01-01'},
            'error': {
                'non_field_errors': [
                    'start_date should be less than or equal to end_date.'
                ]
            },
        },
    )
    @ddt.unpack
    def test_get_invalid_query_params(self, params, error):
        """
        Test the GET method return correct error if any query param value is incorrect.
        """
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error
