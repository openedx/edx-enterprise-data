"""
Test cases for enterprise_admin views
"""
from datetime import datetime
from unittest import mock

import ddt
from mock import patch
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.admin_analytics.database.queries import (
    FactEngagementAdminDashQueries,
    FactEnrollmentAdminDashQueries,
)
from enterprise_data.tests.admin_analytics.mock_analytics_data import (
    TOP_SKILLS,
    TOP_SKILLS_BY_COMPLETIONS,
    TOP_SKILLS_BY_ENROLLMENTS,
)
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import EnterpriseSubsidyBudgetFactory, UserFactory, get_dummy_enterprise_api_data
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


@ddt.ddt
@mark.django_db
class TestEnterpriseAdminAnalyticsAggregatesView(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseAdminAnalyticsAggregatesView.
    """

    def setUp(self):
        """
        Setup method.
        """
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
        self.enrollment_queries = FactEnrollmentAdminDashQueries()
        self.engagement_queries = FactEngagementAdminDashQueries()

    def _mock_run_query(self, query, *args, **kwargs):
        """
        mock implementation of run_query.
        """
        mock_responses = {
            self.enrollment_queries.get_enrollment_date_range_query(): [[
                datetime.strptime('2021-01-01', "%Y-%m-%d"),
                datetime.strptime('2021-12-31', "%Y-%m-%d"),
            ]],
            self.enrollment_queries.get_enrollment_and_course_count_query(): [[
                100, 10
            ]],
            self.enrollment_queries.get_completion_count_query(): [[
                50
            ]],
            self.engagement_queries.get_learning_hours_and_daily_sessions_query(): [[
                100, 10
            ]],
            'SELECT MAX(created) FROM enterprise_learner_enrollment': [[datetime.strptime('2021-01-01', "%Y-%m-%d")]]
        }
        return mock_responses[query]

    def test_get_admin_analytics_aggregates(self):
        """
        Test to get admin analytics aggregates.
        """
        url = reverse('v1:enterprise-admin-analytics-aggregates', kwargs={'enterprise_id': self.enterprise_id})
        with patch('enterprise_data.admin_analytics.data_loaders.run_query', side_effect=self._mock_run_query):
            with patch(
                    'enterprise_data.admin_analytics.database.tables.fact_engagement_admin_dash.run_query',
                    side_effect=self._mock_run_query
            ):
                with patch(
                        'enterprise_data.admin_analytics.database.tables.fact_enrollment_admin_dash.run_query',
                        side_effect=self._mock_run_query
                ):
                    response = self.client.get(url)
                    assert response.status_code == status.HTTP_200_OK
                    assert 'enrolls' in response.json()
                    assert 'courses' in response.json()
                    assert 'completions' in response.json()
                    assert 'hours' in response.json()
                    assert 'sessions' in response.json()
                    assert 'last_updated_at' in response.json()
                    assert 'min_enrollment_date' in response.json()
                    assert 'max_enrollment_date' in response.json()


@ddt.ddt
class TestSkillsStatsAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for EnterpriseAdminAnalyticsSkillsView."""

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

        self.enterprise_uuid = "ee5e6b3a069a4947bb8dd2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-admin-analytics-skills",
            kwargs={"enterprise_id": self.enterprise_uuid},
        )

    @patch('enterprise_data.api.v1.views.enterprise_admin.FactEnrollmentAdminDashTable.get_enrollment_date_range')
    @patch('enterprise_data.api.v1.views.enterprise_admin.SkillsDailyRollupAdminDashTable.get_top_skills')
    @patch('enterprise_data.api.v1.views.enterprise_admin.SkillsDailyRollupAdminDashTable.get_top_skills_by_enrollment')
    @patch('enterprise_data.api.v1.views.enterprise_admin.SkillsDailyRollupAdminDashTable.get_top_skills_by_completion')
    def test_get(
        self,
        mock_get_top_skills_by_completion,
        mock_get_top_skills_by_enrollment,
        mock_get_top_skills,
        mock_get_enrollment_date_range
    ):
        """
        Test the GET method for the EnterpriseAdminAnalyticsSkillsView works.
        """
        mock_get_enrollment_date_range.return_value = ("2020-04-03", "2024-07-04")
        mock_get_top_skills.return_value = TOP_SKILLS
        mock_get_top_skills_by_enrollment.return_value = TOP_SKILLS_BY_ENROLLMENTS
        mock_get_top_skills_by_completion.return_value = TOP_SKILLS_BY_COMPLETIONS

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            "top_skills": [
                {
                    "skill_name": "Python (Programming Language)",
                    "skill_type": "Specialized Skill",
                    "enrolls": 19027.0,
                    "completions": 3004.0,
                },
                {
                    "skill_name": "Data Science",
                    "skill_type": "Specialized Skill",
                    "enrolls": 13756.0,
                    "completions": 1517.0,
                },
                {
                    "skill_name": "Algorithms",
                    "skill_type": "Specialized Skill",
                    "enrolls": 12776.0,
                    "completions": 1640.0,
                },
            ],
            "top_skills_by_enrollments": [
                {
                    "skill_name": "Python (Programming Language)",
                    "subject_name": "business-management",
                    "count": 313.0,
                },
                {
                    "skill_name": "Machine Learning",
                    "subject_name": "business-management",
                    "count": 442.0,
                },
                {
                    "skill_name": "Computer Science",
                    "subject_name": "business-management",
                    "count": 39.0,
                },
            ],
            "top_skills_by_completions": [
                {
                    "skill_name": "Python (Programming Language)",
                    "subject_name": "business-management",
                    "count": 21.0,
                },
                {
                    "skill_name": "SQL (Programming Language)",
                    "subject_name": "business-management",
                    "count": 11.0,
                },
                {
                    "skill_name": "Algorithms",
                    "subject_name": "business-management",
                    "count": 15.0,
                },
            ],
        }

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
class TestEnterpriseBudgetAPI(JWTTestMixin, APITransactionTestCase):
    """Tests for EnterpriseBudgetView."""

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

        self.enterprise_uuid = "ee5e6b3a069a4947bb8dd2dbc323396c"
        self.set_jwt_cookie()

        self.url = reverse(
            "v1:enterprise-budgets",
            kwargs={"enterprise_uuid": self.enterprise_uuid},
        )

        self.enterprise_subsidy_budget = EnterpriseSubsidyBudgetFactory(
            enterprise_customer_uuid=self.enterprise_uuid,
            subsidy_access_policy_uuid='8d6503dd-e40d-42b8-442b-37dd4c5450e3',
            subsidy_access_policy_display_name='test-budget'
        )

    def test_get(self):
        """
        Test the GET method for the EnterpriseBudgetView works.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'subsidy_access_policy_uuid': '8d6503dd-e40d-42b8-442b-37dd4c5450e3',
                'subsidy_access_policy_display_name': 'test-budget',
            }
        ]
