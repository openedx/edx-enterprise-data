"""
Tests for enterprise completions analytics.
"""
from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.tests.admin_analytics.mock_analytics_data import ENROLLMENTS
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
class TestCompletionsStatsAPI(JWTTestMixin, APITransactionTestCase):
    """
    Tests for validating enterprise completions stats endpoint.
    """

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

        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

        self.url = reverse(
            'v1:enterprise-admin-analytics-completions-stats',
            kwargs={'enterprise_uuid': self.enterprise_id},
        )

        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    @patch(
        'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.'
        'get_top_subjects_by_completions'
    )
    @patch(
        'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_top_courses_by_completions'
    )
    @patch(
        'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.'
        'get_completions_time_series_data'
    )
    def test_get(
            self,
            mock_get_completions_time_series_data,
            mock_get_top_courses_by_completions,
            mock_get_top_subjects_by_completions
    ):
        """
        Test the GET method to fetch charts data for enterprise completion works correctly.
        """
        mock_get_completions_time_series_data.return_value = []
        mock_get_top_courses_by_completions.return_value = []
        mock_get_top_subjects_by_completions.return_value = []

        params = {
            'start_date': '2020-01-01',
            'end_date': '2025-08-09',
        }
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'completions_over_time' in data
        assert 'top_courses_by_completions' in data
        assert 'top_subjects_by_completions' in data


@ddt.ddt
class TestCompletionsAPI(JWTTestMixin, APITransactionTestCase):
    """
    Tests for validating list endpoint of enterprise completions.
    """

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

        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

        self.url = reverse(
            'v1:enterprise-admin-analytics-completions',
            kwargs={'enterprise_uuid': self.enterprise_id},
        )

        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    @patch('enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_completion_count')
    @patch('enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_all_completions')
    def test_get(self, mock_get_all_completions, mock_get_completion_count):
        """
        Test the GET method for fetching enterprise completions works correctly.
        """
        mock_get_all_completions.return_value = ENROLLMENTS
        mock_get_completion_count.return_value = len(ENROLLMENTS)

        response = self.client.get(self.url + '?page=1&page_size=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=2&page_size=2"
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 3
        assert data["count"] == 5

    @patch('enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_completion_count')
    @patch('enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_all_completions')
    def test_get_csv(self, mock_get_all_completions, mock_get_completion_count):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEnrollmentsView return correct CSV data.
        """
        mock_get_all_completions.return_value = ENROLLMENTS
        mock_get_completion_count.return_value = len(ENROLLMENTS)
        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response["Content-Type"] == "text/csv"

        # verify the response content
        content = b"".join(response.streaming_content).decode().splitlines()
        assert len(content) == 6

        # Verify CSV header.
        assert 'email,course_title,course_subject,enroll_type,passed_date' == content[0]

        # verify the content
        assert (
            'rebeccanelson@example.com,Re-engineered tangible approach,business-management,certificate,2021-08-25'
            in content
        )
        assert (
            'taylorjames@example.com,Re-engineered tangible approach,business-management,certificate,2021-09-01'
            in content
        )
        assert (
            'ssmith@example.com,Secured static capability,medicine,certificate,'
            in content
        )
        assert (
            'kathleenmartin@example.com,Horizontal solution-oriented hub,social-sciences,certificate,'
            in content
        )
        assert (
            'amber79@example.com,Streamlined zero-defect attitude,communication,certificate,'
            in content
        )
