"""
Tests for clients in enterprise_reporting.
"""
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import responses

from django.conf import settings
from django.test import TestCase

from enterprise_reporting.clients.enterprise import EnterpriseAPIClient


class TestEnterpriseAPIClient(TestCase):
    """
    Test Enterprise API client used to connect to the Enterprise API.
    """

    def setUp(self):
        self.enterprise_customer_uuid = 'test-enterprise-customer-uuid'
        self.reporting_config = {}
        self.api_response = {
            'results': [{
                'enterprise_name': 'Test Enterprise',
                'enterprise_id': 'test-id'
            }]
        }
        self.mocked_get_endpoint = Mock(return_value=self.api_response)
        self.client = EnterpriseAPIClient(  # pylint: disable=attribute-defined-outside-init
            settings.BACKEND_SERVICE_EDX_OAUTH2_KEY,
            settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )
        self.client.API_BASE_URL = 'http://localhost-test:8000/'
        super().setUp()

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_get_all_enterprise_reporting_configs(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 10,
        }
        url = urljoin(self.client.API_BASE_URL + '/', self.client.ENTERPRISE_REPORTING_ENDPOINT)
        responses.add(
            responses.GET,
            url,
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_all_enterprise_reporting_configs()
        assert results['results'] == self.api_response['results']

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_get_enterprise_reporting_configs(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 10,
        }
        url = urljoin(self.client.API_BASE_URL + '/', self.client.ENTERPRISE_REPORTING_ENDPOINT)
        responses.add(
            responses.GET,
            url,
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_enterprise_reporting_configs(self.enterprise_customer_uuid)
        assert results['results'] == self.api_response['results']
