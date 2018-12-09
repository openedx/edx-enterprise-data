# -*- coding: utf-8 -*-
"""
Tests for clients in enterprise_data.
"""
from edx_rest_api_client.exceptions import HttpClientError
from mock import ANY, Mock, mock
from rest_framework.exceptions import NotFound, ParseError

from django.test import TestCase, override_settings

from enterprise_data.clients import EnterpriseApiClient
from test_utils import UserFactory


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
        super(TestEnterpriseApiClient, self).setUp()

    def mock_client(self):
        """
        Set up a mocked Enterprise API Client. Avoiding doing this in setup so we can test __init__.
        """
        self.client = EnterpriseApiClient('test-token')
        setattr(self.client, 'enterprise-learner', Mock(
            get=self.mocked_get_endpoint
        ))

        setattr(self.client, 'enterprise-customer', Mock(
            with_access_to=Mock(get=self.mocked_get_endpoint)
        ))

    @mock.patch('enterprise_data.clients.EdxRestApiClient.__init__')
    def test_inits_client_with_jwt(self, mock_init):
        self.mock_client()
        mock_init.assert_called_with(ANY, jwt='test-token')

    def test_get_enterprise_learner_returns_results_for_user(self):
        self.mock_client()
        results = self.client.get_enterprise_learner(self.user)
        self.mocked_get_endpoint.assert_called_with(username=self.user.username)
        assert(results == self.api_response['results'][0])

    def test_get_enterprise_learner_raises_exception_on_error(self):
        self.mocked_get_endpoint = Mock(side_effect=HttpClientError)
        self.mock_client()
        with self.assertRaises(HttpClientError):
            _ = self.client.get_enterprise_learner(self.user)

    def test_get_enterprise_learner_returns_none_on_empty_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 0,
            'results': []
        })
        self.mock_client()
        results = self.client.get_enterprise_learner(self.user)
        self.assertIsNone(results)

    def test_get_enterprise_learner_raises_not_found_on_no_results(self):
        self.mocked_get_endpoint = Mock(return_value={})
        self.mock_client()
        with self.assertRaises(NotFound):
            _ = self.client.get_enterprise_learner(self.user)

    def test_get_enterprise_learner_raises_parse_error_on_multiple_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 2,
            'results': [{}, {}]
        })
        self.mock_client()
        with self.assertRaises(ParseError):
            _ = self.client.get_enterprise_learner(self.user)

    def test_get_with_access_to_returns_results_for_user(self):
        self.mock_client()
        results = self.client.get_with_access_to(self.user, self.enterprise_id)
        self.mocked_get_endpoint.assert_called_with(
            permissions=[EnterpriseApiClient.ENTERPRISE_DATA_API_GROUP],
            enterprise_id=self.enterprise_id
        )
        assert(results == self.api_response['results'][0])

    def test_get_with_access_to_raises_exception_on_error(self):
        self.mocked_get_endpoint = Mock(side_effect=HttpClientError)
        self.mock_client()
        with self.assertRaises(HttpClientError):
            _ = self.client.get_with_access_to(self.user, self.enterprise_id)

    def test_get_with_access_to_returns_none_on_empty_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 0,
            'results': []
        })
        self.mock_client()
        results = self.client.get_with_access_to(self.user, self.enterprise_id)
        self.assertIsNone(results)

    def test_get_with_access_to_raises_not_found_on_no_results(self):
        self.mocked_get_endpoint = Mock(return_value={})
        self.mock_client()
        with self.assertRaises(NotFound):
            _ = self.client.get_with_access_to(self.user, self.enterprise_id)

    def test_get_with_access_to_raises_parse_error_on_multiple_results(self):
        self.mocked_get_endpoint = Mock(return_value={
            'count': 2,
            'results': [{}, {}]
        })
        self.mock_client()
        with self.assertRaises(ParseError):
            _ = self.client.get_with_access_to(self.user, self.enterprise_id)
