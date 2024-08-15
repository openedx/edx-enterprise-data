"""Unittests for analytics_enrollments.py"""

from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.tests.admin_analytics.mock_analytics_data import (
    ENROLLMENTS,
    LEADERBOARD_RESPONSE,
    engagements_dataframe,
    enrollments_dataframe,
    leaderboard_csv_content,
)
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
            "v1:enterprise-admin-analytics-leaderboard",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.api.v1.views.analytics_leaderboard.fetch_enrollments_cache_expiry_timestamp',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

        fetch_max_engagement_datetime_patcher = patch(
            'enterprise_data.api.v1.views.analytics_leaderboard.fetch_engagements_cache_expiry_timestamp',
            return_value=datetime.now()
        )

        fetch_max_engagement_datetime_patcher.start()
        self.addCleanup(fetch_max_engagement_datetime_patcher.stop)

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

    @patch(
        "enterprise_data.api.v1.views.analytics_leaderboard.fetch_and_cache_enrollments_data"
    )
    @patch(
        "enterprise_data.api.v1.views.analytics_leaderboard.fetch_and_cache_engagements_data"
    )
    def test_get(self, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsLeaderboardView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()

        response = self.client.get(self.url, {"page_size": 2})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data["next"] == f'http://testserver{self.url}?page=2&page_size=2'
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 6
        assert data["count"] == 12
        assert data["results"] == [
            {
                "email": "paul77@example.org",
                "daily_sessions": 1,
                "learning_time_seconds": 15753,
                "learning_time_hours": 4.4,
                "average_session_length": 4.4,
                "course_completions": None,
            },
            {
                "email": "seth57@example.org",
                "daily_sessions": 1,
                "learning_time_seconds": 9898,
                "learning_time_hours": 2.7,
                "average_session_length": 2.7,
                "course_completions": None,
            },
        ]

        # fetch all records
        response = self.client.get(self.url, {"page_size": 20})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] is None
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 1
        assert data["count"] == 12
        assert data["results"] == LEADERBOARD_RESPONSE

    @patch(
        "enterprise_data.api.v1.views.analytics_leaderboard.fetch_and_cache_enrollments_data"
    )
    @patch(
        "enterprise_data.api.v1.views.analytics_leaderboard.fetch_and_cache_engagements_data"
    )
    def test_get_csv(self, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEnrollmentsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()

        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response["Content-Type"] == "text/csv"

        # verify the response content
        content = b"".join(response.streaming_content)
        assert content == leaderboard_csv_content()
