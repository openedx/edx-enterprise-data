"""Unittests for analytics_enrollments.py"""

from datetime import datetime

import ddt
from mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.constants import EngagementChart, ResponseType
from enterprise_data.api.v1.serializers import AdvanceAnalyticsEngagementStatsSerializer as EngagementSerializer
from enterprise_data.tests.admin_analytics.mock_analytics_data import (
    ENGAGEMENT_STATS_CSVS,
    ENGAGEMENTS,
    engagements_csv_content,
    engagements_dataframe,
    enrollments_dataframe,
)
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment

INVALID_CALCULATION_ERROR = (
    f"Calculation must be one of {EngagementSerializer.CALCULATION_CHOICES}"
)
INVALID_GRANULARITY_ERROR = (
    f"Granularity must be one of {EngagementSerializer.GRANULARITY_CHOICES}"
)
INVALID_CSV_ERROR1 = f"chart_type must be one of {EngagementSerializer.CHART_TYPES}"


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

        self.enterprise_uuid = "ee5e6b3a-069a-4947-bb8d-d2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-engagements",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.admin_analytics.utils.fetch_max_enrollment_datetime',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

    def verify_engagement_data(self, results, results_count):
        """Verify the received engagement data."""
        attrs = [
            "email",
            "course_title",
            "activity_date",
            "course_subject",
        ]

        assert len(results) == results_count

        filtered_data = []
        for engagement in ENGAGEMENTS:
            for result in results:
                if engagement["email"] == result["email"]:
                    data = {attr: engagement[attr] for attr in attrs}
                    data["learning_time_hours"] = round(engagement["learning_time_seconds"] / 3600, 1)
                    filtered_data.append(data)
                    break

        received_data = sorted(results, key=lambda x: x["email"])
        expected_data = sorted(filtered_data, key=lambda x: x["email"])
        assert received_data == expected_data

    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_enrollments_data"
    )
    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_engagements_data"
    )
    def test_get(self, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEngagementsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()

        response = self.client.get(self.url, {"page_size": 2})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=2&page_size=2"
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 5
        assert data["count"] == 9
        self.verify_engagement_data(data["results"], 2)

        response = self.client.get(self.url, {"page_size": 2, "page": 2})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] == f"http://testserver{self.url}?page=3&page_size=2"
        assert data["previous"] == f"http://testserver{self.url}?page_size=2"
        assert data["current_page"] == 2
        assert data["num_pages"] == 5
        assert data["count"] == 9
        self.verify_engagement_data(data["results"], 2)

        response = self.client.get(self.url, {"page_size": 2, "page": 5})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] is None
        assert data["previous"] == f"http://testserver{self.url}?page=4&page_size=2"
        assert data["current_page"] == 5
        assert data["num_pages"] == 5
        assert data["count"] == 9
        self.verify_engagement_data(data["results"], 1)

        response = self.client.get(self.url, {"page_size": 9})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["next"] is None
        assert data["previous"] is None
        assert data["current_page"] == 1
        assert data["num_pages"] == 1
        assert data["count"] == 9
        self.verify_engagement_data(data["results"], 9)

    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_enrollments_data"
    )
    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_engagements_data"
    )
    def test_get_csv(self, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsIndividualEngagementsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()
        start_date = enrollments_dataframe().enterprise_enrollment_date.min().strftime('%Y/%m/%d')
        end_date = datetime.now().strftime('%Y/%m/%d')
        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value})
        assert response.status_code == status.HTTP_200_OK

        # verify the response headers
        assert response["Content-Type"] == "text/csv"
        filename = f"""Individual Engagements, {start_date} - {end_date}.csv"""
        assert (
            response["Content-Disposition"] == f'attachment; filename="{filename}"'
        )

        # verify the response content
        content = b"".join(response.streaming_content)
        assert content == engagements_csv_content()

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
        {"params": {"chart_type": "invalid"}, "error": {"chart_type": [INVALID_CSV_ERROR1]}},
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

        self.enterprise_uuid = "ee5e6b3a-069a-4947-bb8d-d2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-engagements-stats",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        fetch_max_enrollment_datetime_patcher = patch(
            'enterprise_data.admin_analytics.utils.fetch_max_enrollment_datetime',
            return_value=datetime.now()
        )

        fetch_max_enrollment_datetime_patcher.start()
        self.addCleanup(fetch_max_enrollment_datetime_patcher.stop)

    def verify_engagement_data(self, results):
        """Verify the received engagement data."""
        attrs = [
            "email",
            "course_title",
            "activity_date",
            "course_subject",
        ]

        filtered_data = []
        for engagement in ENGAGEMENTS:
            for result in results:
                if engagement["email"] == result["email"]:
                    data = {attr: engagement[attr] for attr in attrs}
                    data["learning_time_hours"] = round(engagement["learning_time_seconds"] / 3600, 1)
                    filtered_data.append(data)
                    break

        received_data = sorted(results, key=lambda x: x["email"])
        expected_data = sorted(filtered_data, key=lambda x: x["email"])
        assert received_data == expected_data

    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_enrollments_data"
    )
    @patch(
        "enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_engagements_data"
    )
    def test_get(self, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test the GET method for the AdvanceAnalyticsEnrollmentStatsView works.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            'engagements_over_time': [
                {'activity_date': '2021-07-19T00:00:00', 'enroll_type': 'certificate', 'sum': 0.0},
                {'activity_date': '2021-07-26T00:00:00', 'enroll_type': 'certificate', 'sum': 4.4},
                {'activity_date': '2021-07-27T00:00:00', 'enroll_type': 'certificate', 'sum': 1.2},
                {'activity_date': '2021-08-05T00:00:00', 'enroll_type': 'certificate', 'sum': 3.6},
                {'activity_date': '2021-08-21T00:00:00', 'enroll_type': 'certificate', 'sum': 2.7},
                {'activity_date': '2021-09-02T00:00:00', 'enroll_type': 'certificate', 'sum': 1.3},
                {'activity_date': '2021-09-21T00:00:00', 'enroll_type': 'certificate', 'sum': 1.5},
                {'activity_date': '2022-05-17T00:00:00', 'enroll_type': 'certificate', 'sum': 0.0}
            ],
            'top_courses_by_engagement': [
                {
                    'course_key': 'Kcpr+XoR30',
                    'course_title': 'Assimilated even-keeled focus group',
                    'enroll_type': 'certificate',
                    'count': 0.0
                },
                {
                    'course_key': 'luGg+KNt30',
                    'course_title': 'Synergized reciprocal encoding',
                    'enroll_type': 'certificate',
                    'count': 14.786944444444444
                }
            ],
            'top_subjects_by_engagement': [
                {
                    'course_subject': 'business-management',
                    'enroll_type': 'certificate',
                    'count': 14.786944444444444
                },
                {
                    'course_subject': 'engineering',
                    'enroll_type': 'certificate',
                    'count': 0.0
                }
            ]
        }

    @patch("enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_enrollments_data")
    @patch("enterprise_data.api.v1.views.analytics_engagements.fetch_and_cache_engagements_data")
    @ddt.data(
        EngagementChart.ENGAGEMENTS_OVER_TIME.value,
        EngagementChart.TOP_COURSES_BY_ENGAGEMENTS.value,
        EngagementChart.TOP_SUBJECTS_BY_ENGAGEMENTS.value,
    )
    def test_get_csv(self, chart_type, mock_fetch_and_cache_engagements_data, mock_fetch_and_cache_enrollments_data):
        """
        Test that AdvanceAnalyticsEngagementStatsView return correct CSV data.
        """
        mock_fetch_and_cache_enrollments_data.return_value = enrollments_dataframe()
        mock_fetch_and_cache_engagements_data.return_value = engagements_dataframe()
        response = self.client.get(self.url, {"response_type": ResponseType.CSV.value, "chart_type": chart_type})
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        # verify the response content
        assert response.content == ENGAGEMENT_STATS_CSVS[chart_type]

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
        {"params": {"chart_type": "invalid"}, "error": {"chart_type": [INVALID_CSV_ERROR1]}},
    )
    @ddt.unpack
    def test_get_invalid_query_params(self, params, error):
        """
        Test the GET method return correct error if any query param value is incorrect.
        """
        response = self.client.get(self.url, params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == error
