"""Unitest for EnterpriseAdminCompletionsStatsView."""
from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.utils import ChartType
from enterprise_data.tests.admin_analytics.mock_analytics_data import (
    COMPLETIONS_STATS_CSVS,
    ENROLLMENTS,
    enrollments_dataframe,
)
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
class TestCompletionstStatsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for EnterrpiseAdminCompletionsStatsView."""

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

        self.enterprise_id = "ee5e6b3a-069a-4947-bb8d-d2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-completions-stats",
            kwargs={"enterprise_id": self.enterprise_id},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.api.v1.views.enterprise_completions.fetch_max_enrollment_datetime',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

    @patch(
        "enterprise_data.api.v1.views.enterprise_completions.fetch_and_cache_enrollments_data"
    )
    def test_get(self, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the EnterrpiseAdminCompletionsStatsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()

        params = {
            "start_date": "2020-01-01",
            "end_date": "2025-08-09",
            "calculation": "Running Total",
            "granularity": "Daily",
        }
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            "completions_over_time": [
                {
                    "passed_date": "2021-08-25T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "passed_date": "2021-09-01T00:00:00",
                    "enroll_type": "certificate",
                    "count": 2,
                },
            ],
            "top_courses_by_completions": [
                {
                    "course_key": "hEmW+tvk03",
                    "course_title": "Re-engineered tangible approach",
                    "enroll_type": "certificate",
                    "count": 2,
                }
            ],
            "top_subjects_by_completions": [
                {
                    "course_subject": "business-management",
                    "enroll_type": "certificate",
                    "count": 2,
                }
            ],
        }

    @patch("enterprise_data.api.v1.views.enterprise_completions.fetch_and_cache_enrollments_data")
    @ddt.data(
        ChartType.COMPLETIONS_OVER_TIME.value,
        ChartType.TOP_COURSES_BY_COMPLETIONS.value,
        ChartType.TOP_SUBJECTS_BY_COMPLETIONS.value,
    )
    def test_get_csv(self, chart_type, mock_fetch_and_cache_enrollments_data):
        """
        Test that EnterrpiseAdminCompletionsStatsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        params = {
            'start_date': '2020-01-01',
            'end_date': '2025-08-09',
            'calculation': 'Running Total',
            'granularity': 'Daily',
            'response_type': 'csv',
            'chart_type': chart_type,
        }
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        # verify the response content
        assert response.content == COMPLETIONS_STATS_CSVS[chart_type]


@ddt.ddt
class TestCompletionstAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for EnterrpiseAdminCompletionsView."""

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

        self.enterprise_id = "ee5e6b3a-069a-4947-bb8d-d2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-completions",
            kwargs={"enterprise_id": self.enterprise_id},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.api.v1.views.enterprise_completions.fetch_max_enrollment_datetime',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

    def verify_enrollment_data(self, results, results_count):
        """Verify the received enrollment data."""
        attrs = [
            "email",
            "course_title",
            "course_subject",
            "passed_date",
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
        "enterprise_data.api.v1.views.enterprise_completions.fetch_and_cache_enrollments_data"
    )
    def test_get(self, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the EnterrpiseAdminCompletionsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()

        response = self.client.get(self.url, {"page": 1, "page_size": 1})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=2&page_size=1"
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 2
        assert data["count"] == 2
        self.verify_enrollment_data(data["results"], 1)
