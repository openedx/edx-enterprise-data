"""
Tests for leaderboard API.
"""

from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.tests.admin_analytics.mock_analytics_data import ENROLLMENTS, LEADERBOARD_RESPONSE
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
class TestLeaderboardAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for AdvanceAnalyticsLeaderboardView."""

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

        self.enterprise_uuid = "ee5e6b3a-069a-4947-bb8d-d2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-leaderboard-list",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )
        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    def verify_enrollment_data(self, results, results_count):
        """Verify the received enrollment data."""
        attrs = [
            "email",
            "course_title",
            "course_subject",
            "enroll_type",
            "enterprise_enrollment_date",
        ]

        assert len(results) == results_count

        filtered_data = []
        for enrollment in ENROLLMENTS:
            for result in results:
                if enrollment["email"] == result["email"]:
                    filtered_data.append({attr: enrollment[attr] for attr in attrs})
                    break

        received_data = sorted(results, key=lambda x: x["email"])
        expected_data = sorted(filtered_data, key=lambda x: x["email"])
        assert received_data == expected_data

    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_leaderboard_data_count')
    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_all_leaderboard_data')
    def test_get(self, mock_get_all_leaderboard_data, mock_get_leaderboard_data_count):
        """
        Test the GET method for the AdvanceAnalyticsLeaderboardView works.
        """
        mock_get_all_leaderboard_data.return_value = LEADERBOARD_RESPONSE
        mock_get_leaderboard_data_count.return_value = len(LEADERBOARD_RESPONSE)
        response = self.client.get(self.url + '?page_size=2')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/json'
        data = response.json()
        assert data['next'] == f'http://testserver{self.url}?page=2&page_size=2'
        assert data['previous'] is None
        assert data['current_page'] == 1
        assert data['num_pages'] == 6
        assert data['count'] == 12

        # fetch all records
        response = self.client.get(self.url + '?page_size=20')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] is None
        assert data['previous'] is None
        assert data['current_page'] == 1
        assert data['num_pages'] == 1
        assert data['count'] == 12

    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_leaderboard_data_count')
    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_all_leaderboard_data')
    def test_get_csv(self, mock_get_all_leaderboard_data, mock_get_leaderboard_data_count):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEnrollmentsView return correct CSV data.
        """
        mock_get_all_leaderboard_data.return_value = LEADERBOARD_RESPONSE[:5]
        mock_get_leaderboard_data_count.return_value = 5
        response = self.client.get(self.url, {'response_type': ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response['Content-Type'] == 'text/csv'

        content = b"".join(response.streaming_content).decode().splitlines()
        assert len(content) == 6

        # Verify CSV header.
        assert 'email,learning_time_hours,session_count,average_session_length,course_completion_count' == content[0]

        # verify the content
        assert 'paul77@example.org,4.4,,4.4,' in content
        assert 'seth57@example.org,2.7,,2.7,' in content
        assert 'weaverpatricia@example.net,2.6,,2.6,' in content
        assert 'webertodd@example.com,1.5,,1.5,' in content
        assert 'yferguson@example.net,1.3,,1.3,' in content
