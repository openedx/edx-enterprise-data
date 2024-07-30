"""
Test cases for enterprise_admin views
"""
from unittest import mock

import ddt
from mock import patch
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import (
    UserFactory,
    get_dummy_engagements_data,
    get_dummy_enrollments_data,
    get_dummy_enterprise_api_data,
)
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

    def _mock_run_query(self, query):
        """
        mock implementation of run_query.
        """
        if 'fact_enrollment_admin_dash' in query:
            return [
                list(item.values()) for item in get_dummy_enrollments_data(self.enterprise_id, 15)
            ]
        else:
            return [
                list(item.values()) for item in get_dummy_engagements_data(self.enterprise_id, 15)
            ]

    def test_get_admin_analytics_aggregates(self):
        """
        Test to get admin analytics aggregates.
        """
        url = reverse('v1:enterprise-admin-analytics-aggregates', kwargs={'enterprise_id': self.enterprise_id})
        with patch('enterprise_data.admin_analytics.data_loaders.run_query', side_effect=self._mock_run_query):
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
