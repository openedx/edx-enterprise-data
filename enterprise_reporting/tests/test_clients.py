"""
Tests for clients in enterprise_reporting.
"""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import responses

from django.conf import settings
from django.test import TestCase

from enterprise_reporting.clients.enterprise import EnterpriseAPIClient, EnterpriseCatalogAPIClient


class TestEnterpriseAPIClient(TestCase):
    """
    Test Enterprise API client used to connect to the Enterprise API.
    """

    def setUp(self):
        self.enterprise_customer_uuid = 'test-enterprise-customer-uuid'
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
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
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
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
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


class TestEnterpriseCatalogAPIClient(TestCase):
    """
    Test Enterprise Catalog API client used to connect to the Enterprise API.
    """

    def setUp(self):
        self.enterprise_customer_uuid = 'test-enterprise-customer-uuid'
        self.program_uuid = 'test-program_uuid'
        self.client = EnterpriseCatalogAPIClient(  # pylint: disable=attribute-defined-outside-init
            settings.BACKEND_SERVICE_EDX_OAUTH2_KEY,
            settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )
        self.client.API_BASE_URL = 'http://localhost-test:8000/'
        super().setUp()

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_get_customer_catalogs(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
        api_response = {
            'results': [{
                'enterprise_name': 'Test Enterprise',
                'enterprise_id': 'test-id'
            }]
        }
        mocked_get_endpoint = Mock(return_value=api_response)
        url = urljoin(self.client.API_BASE_URL, self.client.ENTERPRISE_CATALOGS_ENDPOINT)
        url = f'{url}?enterprise_customer={self.enterprise_customer_uuid}&page_size=1000'
        responses.add(
            responses.GET,
            url,
            json=mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_customer_catalogs(self.enterprise_customer_uuid)
        assert results['results'] == api_response['results']

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_get_content_metadata(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
        metadata_api_response = {
            'results': [{
                'uuid': self.program_uuid,
                'content_type': 'program',
            }]
        }
        mocked_get_metadata_endpoint = Mock(return_value=metadata_api_response)
        url_path = self.client.GET_CONTENT_METADATA_ENDPOINT.format(self.enterprise_customer_uuid)
        url = urljoin(
            self.client.API_BASE_URL,
            f'{url_path}?page_size=1000'
        )
        responses.add(
            responses.GET,
            url,
            json=mocked_get_metadata_endpoint(),
            status=200,
            content_type='application/json'
        )
        request_catalogs = {
            'results': [{
                'uuid': self.enterprise_customer_uuid,
            }]
        }
        results = self.client.get_content_metadata(request_catalogs)
        assert results[0]['uuid'] == metadata_api_response['results'][0]['uuid']
        assert results[0]['content_type'] == metadata_api_response['results'][0]['content_type']

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_accepted_subject_in_content_metadata(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
        metadata_api_response = {
            'results': [{
                'key': 'test_key',
                'uuid': 'test_course_uuid',
                'content_type': 'course',
                'subjects': [
                    {
                        'name': 'Business & Management',
                    },
                    'Communication'
                ],
            }]
        }
        mocked_get_metadata_endpoint = Mock(return_value=metadata_api_response)
        url_path = self.client.GET_CONTENT_METADATA_ENDPOINT.format(self.enterprise_customer_uuid)
        url = urljoin(
            self.client.API_BASE_URL,
            f'{url_path}?page_size=1000'
        )
        responses.add(
            responses.GET,
            url,
            json=mocked_get_metadata_endpoint(),
            status=200,
            content_type='application/json'
        )
        request_catalogs = {
            'results': [{
                'uuid': self.enterprise_customer_uuid,
            }]
        }
        results = self.client.get_content_metadata(request_catalogs)
        assert results[0]['uuid'] == metadata_api_response['results'][0]['uuid']

    @responses.activate
    @patch('enterprise_reporting.clients.get_oauth_access_token')
    def test_rejected_subject_format_in_content_metadata(self, mock_get_oauth_access_token):
        mock_get_oauth_access_token.return_value = ['test_access_token', datetime.now() + timedelta(minutes=60)]
        metadata_api_response = {
            'results': [{
                'key': 'test_key',
                'uuid': 'test_course_uuid',
                'content_type': 'course',
                'subjects': [
                    [
                        'Communication'
                    ]
                ],
            }]
        }
        mocked_get_metadata_endpoint = Mock(return_value=metadata_api_response)
        url_path = self.client.GET_CONTENT_METADATA_ENDPOINT.format(self.enterprise_customer_uuid)
        url = urljoin(
            self.client.API_BASE_URL,
            f'{url_path}?page_size=1000'
        )
        responses.add(
            responses.GET,
            url,
            json=mocked_get_metadata_endpoint(),
            status=200,
            content_type='application/json'
        )
        request_catalogs = {
            'results': [{
                'uuid': self.enterprise_customer_uuid,
            }]
        }
        expected_error_message = "Subject is not a string or a dictionary: ['Communication']"
        try:
            results = self.client.get_content_metadata(request_catalogs)
        except Exception as e:
            self.assertEqual(str(e), expected_error_message)
