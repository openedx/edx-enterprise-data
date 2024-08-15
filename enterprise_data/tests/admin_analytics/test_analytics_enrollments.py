"""Unittests for analytics_enrollments.py"""

from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import EnrollmentChart, ResponseType
from enterprise_data.api.v1.serializers import AdvanceAnalyticsEnrollmentStatsSerializer as EnrollmentStatsSerializer
from enterprise_data.api.v1.serializers import AdvanceAnalyticsQueryParamSerializer
from enterprise_data.tests.admin_analytics.mock_analytics_data import (
    ENROLLMENT_STATS_CSVS,
    ENROLLMENTS,
    enrollments_csv_content,
    enrollments_dataframe,
)
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment

INVALID_CALCULATION_ERROR = (
    f"Calculation must be one of {AdvanceAnalyticsQueryParamSerializer.CALCULATION_CHOICES}"
)
INVALID_GRANULARITY_ERROR = (
    f"Granularity must be one of {AdvanceAnalyticsQueryParamSerializer.GRANULARITY_CHOICES}"
)
INVALID_RESPONSE_TYPE_ERROR = f"response_type must be one of {AdvanceAnalyticsQueryParamSerializer.RESPONSE_TYPES}"
INVALID_CHART_TYPE_ERROR = f"chart_type must be one of {EnrollmentStatsSerializer.CHART_TYPES}"


@ddt.ddt
class TestIndividualEnrollmentsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for AdvanceAnalyticsIndividualEnrollmentsView."""

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
            "v1:enterprise-admin-analytics-enrollments",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.fetch_enrollments_cache_expiry_timestamp',
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
        "enterprise_data.api.v1.views.analytics_enrollments.fetch_and_cache_enrollments_data"
    )
    def test_get(self, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEnrollmentsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()

        response = self.client.get(self.url, {"page_size": 2})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=2&page_size=2"
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 3
        assert data["count"] == 5
        self.verify_enrollment_data(data["results"], 2)

        response = self.client.get(self.url, {"page_size": 2, "page": 2})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=3&page_size=2"
        assert data["previous"] == f"http://testserver{self.url}?page_size=2"
        assert data["current_page"] == 2
        assert data["num_pages"] == 3
        assert data["count"] == 5
        self.verify_enrollment_data(data["results"], 2)

        response = self.client.get(self.url, {"page_size": 2, "page": 3})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data["next"] is None
        assert data["previous"] == f"http://testserver{self.url}?page=2&page_size=2"
        assert data["current_page"] == 3
        assert data["num_pages"] == 3
        assert data["count"] == 5
        self.verify_enrollment_data(data["results"], 1)

        response = self.client.get(self.url, {"page_size": 5})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data["next"] is None
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 1
        assert data["count"] == 5
        self.verify_enrollment_data(data["results"], 5)

    @patch(
        "enterprise_data.api.v1.views.analytics_enrollments.fetch_and_cache_enrollments_data"
    )
    def test_get_csv(self, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEnrollmentsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response["Content-Type"] == "text/csv"

        # verify the response content
        content = b"".join(response.streaming_content)
        assert content == enrollments_csv_content()

    @ddt.data(
        {
            "params": {"start_date": 1},
            "error": {
                "start_date": [
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                ]
            },
        },
        {
            "params": {"end_date": 2},
            "error": {
                "end_date": [
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                ]
            },
        },
        {
            "params": {"start_date": "2024-01-01", "end_date": "2023-01-01"},
            "error": {
                "non_field_errors": [
                    "start_date should be less than or equal to end_date."
                ]
            },
        },
        {
            "params": {"calculation": "invalid"},
            "error": {"calculation": [INVALID_CALCULATION_ERROR]},
        },
        {
            "params": {"granularity": "invalid"},
            "error": {"granularity": [INVALID_GRANULARITY_ERROR]},
        },
        {"params": {"response_type": "invalid"}, "error": {"response_type": [INVALID_RESPONSE_TYPE_ERROR]}},
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
class TestEnrollmentStatsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for AdvanceAnalyticsEnrollmentStatsView."""

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
            "v1:enterprise-admin-analytics-enrollments-stats",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.fetch_enrollments_cache_expiry_timestamp',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

    def verify_enrollment_data(self, results):
        """Verify the received enrollment data."""
        attrs = [
            "email",
            "course_title",
            "course_subject",
            "enroll_type",
            "enterprise_enrollment_date",
        ]

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
        "enterprise_data.api.v1.views.analytics_enrollments.fetch_and_cache_enrollments_data"
    )
    def test_get(self, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsEnrollmentStatsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = response.json()
        assert data == {
            "enrollments_over_time": [
                {
                    "enterprise_enrollment_date": "2020-04-03T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "enterprise_enrollment_date": "2020-04-08T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "enterprise_enrollment_date": "2021-05-11T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "enterprise_enrollment_date": "2021-07-03T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "enterprise_enrollment_date": "2021-07-04T00:00:00",
                    "enroll_type": "certificate",
                    "count": 1,
                },
            ],
            "top_courses_by_enrollments": [
                {"course_key": "NOGk+UVD31", "enroll_type": "certificate", "count": 1},
                {"course_key": "QWXx+Jqz64", "enroll_type": "certificate", "count": 1},
                {"course_key": "hEmW+tvk03", "enroll_type": "certificate", "count": 2},
                {"course_key": "qZJC+KFX86", "enroll_type": "certificate", "count": 1},
            ],
            "top_subjects_by_enrollments": [
                {
                    "course_subject": "business-management",
                    "enroll_type": "certificate",
                    "count": 2,
                },
                {
                    "course_subject": "communication",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "course_subject": "medicine",
                    "enroll_type": "certificate",
                    "count": 1,
                },
                {
                    "course_subject": "social-sciences",
                    "enroll_type": "certificate",
                    "count": 1,
                },
            ],
        }

    @patch("enterprise_data.api.v1.views.analytics_enrollments.fetch_and_cache_enrollments_data")
    @ddt.data(
        EnrollmentChart.ENROLLMENTS_OVER_TIME.value,
        EnrollmentChart.TOP_COURSES_BY_ENROLLMENTS.value,
        EnrollmentChart.TOP_SUBJECTS_BY_ENROLLMENTS.value,
    )
    def test_get_csv(self, chart_type, mock_fetch_and_cache_enrollments_data):
        """
        Test that AdvanceAnalyticsEnrollmentStatsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()

        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value, "chart_type": chart_type})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        # verify the response content
        assert response.content == ENROLLMENT_STATS_CSVS[chart_type]

    @ddt.data(
        {
            "params": {"start_date": 1},
            "error": {
                "start_date": [
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                ]
            },
        },
        {
            "params": {"end_date": 2},
            "error": {
                "end_date": [
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
                ]
            },
        },
        {
            "params": {"start_date": "2024-01-01", "end_date": "2023-01-01"},
            "error": {
                "non_field_errors": [
                    "start_date should be less than or equal to end_date."
                ]
            },
        },
        {
            "params": {"calculation": "invalid"},
            "error": {"calculation": [INVALID_CALCULATION_ERROR]},
        },
        {
            "params": {"granularity": "invalid"},
            "error": {"granularity": [INVALID_GRANULARITY_ERROR]},
        },
        {"params": {"chart_type": "invalid"}, "error": {"chart_type": [INVALID_CHART_TYPE_ERROR]}},
    )
    @ddt.unpack
    def test_get_invalid_query_params(self, params, error):
        """
        Test the GET method return correct error if any query param value is incorrect.
        """
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error
