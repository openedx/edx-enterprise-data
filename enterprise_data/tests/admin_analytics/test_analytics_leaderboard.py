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
        assert data['num_pages'] == 7
        assert data['count'] == 14

        # fetch all records
        response = self.client.get(self.url + '?page_size=20')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['next'] is None
        assert data['previous'] is None
        assert data['current_page'] == 1
        assert data['num_pages'] == 1
        assert data['count'] == 14
        assert data['count'] == len(LEADERBOARD_RESPONSE)
        assert data['num_pages'] == 1 # ceil(count/page_size)

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
        assert len(content) == 6  # header + 5 data rows

        # Verify CSV header
        assert 'email,learning_time_hours,session_count,average_session_length,course_completion_count' == content[0]

        # Verify content — values should reflect unfiltered learning hours
        assert 'paul77@example.org,4.4,,4.4,' in content
        assert 'seth57@example.org,2.7,,2.7,' in content

    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_leaderboard_data_count')
    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_all_leaderboard_data')
    def test_get_leaderboard_uses_unfiltered_engagement_data(
        self,
        mock_get_all_leaderboard_data,
        mock_get_leaderboard_data_count,
    ):
        """
        Test leaderboard API uses unfiltered engagement data.

        Leaderboard should not be filtered by is_engaged or has_passed.
        """
        mock_get_all_leaderboard_data.return_value = LEADERBOARD_RESPONSE
        mock_get_leaderboard_data_count.return_value = len(LEADERBOARD_RESPONSE)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

        mock_get_all_leaderboard_data.assert_called_once()
        _, kwargs = mock_get_all_leaderboard_data.call_args

        assert 'is_engaged' not in kwargs
        assert 'has_passed' not in kwargs

    @patch(
        'enterprise_data.admin_analytics.database.tables.'

    'FactEngagementAdminDashTable._get_engagement_data_for_leaderboard'
    )
    @patch(
        'enterprise_data.admin_analytics.database.tables.'

    'FactEngagementAdminDashTable._get_completion_data_for_leaderboard_query'
    )
    @patch(
        'enterprise_data.admin_analytics.database.tables.'

    'FactEngagementAdminDashTable.get_leaderboard_data_count'
    )
    def test_get_includes_non_engaged_learners(
        self, mock_count, mock_completion, mock_engagement
    ):
        """
        Test that leaderboard includes learners with is_engaged=0.
        After ENT-11979, the is_engaged filter is removed so all learners
        with any learning time should appear in the leaderboard.
        """
        # Mock engagement data including both engaged and non-engaged learners
        mock_engagement.return_value = [
            {
                "email": "engaged_learner@example.com",
                "sessions": 1,
                "learning_time_hours": 4.4,
                "average_session_length": 4.4,
            },
            {
                "email": "non_engaged_learner@example.com",
                "sessions": 0,
                "learning_time_hours": 0.006,  # browsing time, not "engaged"
                "average_session_length": 0.006,
            },
        ]
        mock_completion.return_value = []
        mock_count.return_value = 2

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Both engaged and non-engaged learners should appear
        assert data['count'] == 2
        emails = [r['email'] for r in data['results']]
        assert 'engaged_learner@example.com' in emails
        assert 'non_engaged_learner@example.com' in emails

    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_leaderboard_data_count')
    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_all_leaderboard_data')
    def test_get_includes_non_passed_completions(
        self, mock_get_all_leaderboard_data, mock_get_leaderboard_data_count
    ):
        """
        Test that leaderboard course_completion_count includes enrollments
        where has_passed=0. After ENT-11979, the has_passed filter is removed.
        """
        mock_data = [
            {
                "email": "learner1@example.com",
                "sessions": 1,
                "learning_time_hours": 3.0,
                "average_session_length": 3.0,
                "course_completion_count": 3,  # includes passed + not passed
            },
        ]
        mock_get_all_leaderboard_data.return_value = mock_data
        mock_get_leaderboard_data_count.return_value = 1

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # course_completion_count should include all enrollments, not just passed
        assert data['results'][0]['course_completion_count'] == 3

    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_leaderboard_data_count')
    @patch('enterprise_data.admin_analytics.database.tables.FactEngagementAdminDashTable.get_all_leaderboard_data')
    def test_get_csv_includes_non_engaged_learners(
        self, mock_get_all_leaderboard_data, mock_get_leaderboard_data_count
    ):
        """
        Test that CSV download includes non-engaged learners after ENT-11979.
        """
        mock_data = [
            {
                "email": "engaged@example.com",
                "sessions": 1,
                "learning_time_hours": 4.4,
                "average_session_length": 4.4,
                "course_completion_count": 1,
            },
            {
                "email": "browsing_only@example.com",
                "sessions": 0,
                "learning_time_hours": 0.5,  # browsing time only
                "average_session_length": 0.5,
                "course_completion_count": None,
            },
        ]
        mock_get_all_leaderboard_data.return_value = mock_data
        mock_get_leaderboard_data_count.return_value = 2

        response = self.client.get(self.url, {'response_type': ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        content = b"".join(response.streaming_content).decode().splitlines()
        assert len(content) == 3  # header + 2 data rows

        # Both learners should appear in CSV
        assert 'engaged@example.com' in content[1] or 'engaged@example.com' in content[2]
        assert 'browsing_only@example.com' in content[1] or 'browsing_only@example.com' in content[2]
