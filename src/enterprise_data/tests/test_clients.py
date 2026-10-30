"""
Tests for clients in enterprise_data.
"""
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import responses
from requests.exceptions import HTTPError
from rest_framework.exceptions import NotFound, ParseError

from django.conf import settings
from django.test import TestCase

from enterprise_data.clients import EnterpriseApiClient
from enterprise_data.tests.test_utils import UserFactory, get_dummy_enterprise_api_data


class TestEnterpriseApiClient(TestCase):
    """
    Test Enterprise API client used to connect to LMS enterprise endpoints
    """

    def setUp(self):
        self.user = UserFactory()
        self.enterprise_id = '0395b02f-6b29-42ed-9a41-45f3dff8349c'
        self.api_response = {
            'count': 1,
            'results': [{
                'enterprise_name': 'Test Enterprise',
                'enterprise_id': 'test-id'
            }]
        }
        self.mocked_get_endpoint = Mock(return_value=self.api_response)
        super().setUp()

    def mock_client(self):
        """
        Set up a mocked Enterprise API Client. Avoiding doing this in setup so we can test __init__.
        """
        self.client = EnterpriseApiClient(  # pylint: disable=attribute-defined-outside-init
            settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL,
            settings.BACKEND_SERVICE_EDX_OAUTH2_KEY,
            settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )

        responses.add(
            responses.POST,
            urljoin(settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL + '/', 'access_token'),
            status=200,
            json={
                'access_token': 'test_access_token',
                'expires_in': 10,
            },
            content_type='application/json'
        )

    @responses.activate
    def test_get_enterprise_learner_returns_results_for_user(self):
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/enterprise-learner'),
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_enterprise_learner(self.user)
        assert results == self.api_response['results'][0]

    @responses.activate
    def test_get_enterprise_learner_raises_exception_on_error(self):
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/enterprise-learner'),
            json=self.mocked_get_endpoint(),
            status=404,
            content_type='application/json'
        )
        with self.assertRaises(HTTPError):
            _ = self.client.get_enterprise_learner(self.user)

    @responses.activate
    def test_get_enterprise_learner_returns_none_on_empty_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 0,
            'results': []
        })
        self.mock_client()

        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/enterprise-learner'),
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_enterprise_learner(self.user)
        self.assertIsNone(results)

    @responses.activate
    def test_get_enterprise_learner_raises_not_found_on_no_results(self):
        self.mocked_get_endpoint = Mock(return_value={})
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/enterprise-learner'),
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        with self.assertRaises(NotFound):
            _ = self.client.get_enterprise_learner(self.user)

    @responses.activate
    def test_get_enterprise_learner_raises_parse_error_on_multiple_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 2,
            'results': [{}, {}]
        })
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/enterprise-learner'),
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        with self.assertRaises(ParseError):
            _ = self.client.get_enterprise_learner(self.user)

    @responses.activate
    def test_get_enterprise_customer_returns_results_for_user(self):
        self.mocked_get_endpoint = Mock(return_value=get_dummy_enterprise_api_data())
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', f'enterprise/api/v1/enterprise-customer/{self.enterprise_id}'),
            json=self.mocked_get_endpoint(),
            status=200,
            content_type='application/json'
        )
        results = self.client.get_enterprise_customer(self.enterprise_id)
        assert results == self.mocked_get_endpoint()

    @responses.activate
    def test_get_enterprise_customer_raises_exception_on_error(self):
        self.mocked_get_endpoint = Mock(return_value=get_dummy_enterprise_api_data())
        self.mock_client()
        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', f'enterprise/api/v1/enterprise-customer/{self.enterprise_id}'),
            json=self.mocked_get_endpoint(),
            status=404,
            content_type='application/json'
        )
        with self.assertRaises(HTTPError):
            _ = self.client.get_enterprise_customer(self.enterprise_id)

    @responses.activate
    @patch('enterprise_data.clients.TieredCache')
    def test_get_enterprise_customer_returns_results_from_cashe(self, tired_cache_mock):
        mocked_value = get_dummy_enterprise_api_data()
        self.mock_client()
        tired_cache_mock.get_cached_response.return_value = Mock(
            value=mocked_value,
            is_found=True
        )
        results = self.client.get_enterprise_customer(self.enterprise_id)
        tired_cache_mock.get_cached_response.assert_called_once()
        assert results == mocked_value
