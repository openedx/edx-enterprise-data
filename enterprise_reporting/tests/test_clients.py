"""
Tests for clients in enterprise_reporting.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import urljoin

import responses

from django.conf import settings
from django.test import TestCase, override_settings

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


class TestGetSnowflakeConnectionReporting(TestCase):
    """Tests for the module-level _get_snowflake_connection in enterprise_reporting."""

    _MODULE = 'enterprise_reporting.clients.snowflake'

    def _patch_snowflake(self, connector=None):
        """Return a context manager that replaces the module-level _snowflake namespace."""
        from types import SimpleNamespace
        mock_connector = connector or MagicMock()
        mock_conn = MagicMock()
        mock_connector.connect.return_value = mock_conn
        ns = SimpleNamespace(connector=mock_connector)
        return patch(f'{self._MODULE}._snowflake', ns), mock_connector, mock_conn

    @patch(f'{_MODULE}._serialization')
    @patch(f'{_MODULE}._default_backend')
    @override_settings(
        SNOWFLAKE_SERVICE_USER='svc_user',
        SNOWFLAKE_SERVICE_PRIVKEY='-----BEGIN ENCRYPTED PRIVATE KEY-----\nfake\n-----END ENCRYPTED PRIVATE KEY-----',
        SNOWFLAKE_SERVICE_PASSPHRASE='s3cr3t',
        SNOWFLAKE_ACCOUNT='myaccount',
        SNOWFLAKE_ROLE='MY_ROLE',
    )
    def test_connects_with_private_key(self, mock_backend, mock_serialization):
        """_get_snowflake_connection loads the PEM key and calls connector.connect."""
        from enterprise_reporting.clients.snowflake import _get_snowflake_connection
        mock_key = MagicMock()
        mock_serialization.load_pem_private_key.return_value = mock_key
        mock_key.private_bytes.return_value = b'DER_BYTES'
        mock_connector = MagicMock()
        patcher, _, _ = self._patch_snowflake(connector=mock_connector)
        with patcher:
            _get_snowflake_connection()
        mock_connector.connect.assert_called_once_with(
            user='svc_user',
            account='myaccount',
            private_key=b'DER_BYTES',
            role='MY_ROLE',
        )

    @override_settings(SNOWFLAKE_SERVICE_USER='', SNOWFLAKE_SERVICE_PRIVKEY='k', SNOWFLAKE_SERVICE_PASSPHRASE='p')
    def test_raises_when_user_missing(self):
        from enterprise_reporting.clients.snowflake import _get_snowflake_connection
        with self.assertRaises(ValueError, msg='SNOWFLAKE_SERVICE_USER must be configured'):
            _get_snowflake_connection()

    @override_settings(SNOWFLAKE_SERVICE_USER='u', SNOWFLAKE_SERVICE_PRIVKEY='', SNOWFLAKE_SERVICE_PASSPHRASE='p')
    def test_raises_when_privkey_missing(self):
        from enterprise_reporting.clients.snowflake import _get_snowflake_connection
        with self.assertRaises(ValueError, msg='SNOWFLAKE_SERVICE_PRIVKEY must be configured'):
            _get_snowflake_connection()

    @override_settings(SNOWFLAKE_SERVICE_USER='u', SNOWFLAKE_SERVICE_PRIVKEY='k', SNOWFLAKE_SERVICE_PASSPHRASE='')
    def test_raises_when_passphrase_missing(self):
        from enterprise_reporting.clients.snowflake import _get_snowflake_connection
        with self.assertRaises(ValueError, msg='SNOWFLAKE_SERVICE_PASSPHRASE must be configured'):
            _get_snowflake_connection()


class TestSnowflakeClient(TestCase):
    """Tests for the Snowflake client used in enterprise_reporting."""

    _PATCH = 'enterprise_reporting.clients.snowflake._get_snowflake_connection'

    def _make_connection(self, rows=None):
        """Return a mock Snowflake connection whose cursor yields *rows*."""
        cursor = MagicMock()
        cursor.execute.return_value = iter(rows or [])
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    @patch(_PATCH)
    def test_connect_opens_connection_and_cursor(self, mock_factory):
        """connect() stores connection and cursor on the instance."""
        from enterprise_reporting.clients.snowflake import SnowflakeClient
        conn, cursor = self._make_connection()
        mock_factory.return_value = conn

        client = SnowflakeClient()
        client.connect()

        mock_factory.assert_called_once_with()
        assert client.connection is conn
        assert client.cursor is cursor

    @patch(_PATCH)
    def test_close_connection_closes_cursor_and_connection(self, mock_factory):
        """close_connection() closes both and resets them to None."""
        from enterprise_reporting.clients.snowflake import SnowflakeClient
        conn, cursor = self._make_connection()
        mock_factory.return_value = conn

        client = SnowflakeClient()
        client.connect()
        client.close_connection()

        cursor.close.assert_called_once()
        conn.close.assert_called_once()
        assert client.connection is None
        assert client.cursor is None

    @patch(_PATCH)
    def test_stream_results_yields_formatted_rows(self, mock_factory):
        """stream_results() formats datetime values and passes others through."""
        from enterprise_reporting.clients.snowflake import SnowflakeClient
        dt = datetime(2024, 1, 15, 10, 30, 0)
        conn, cursor = self._make_connection(rows=[(dt, 'hello', 42)])
        mock_factory.return_value = conn

        client = SnowflakeClient()
        client.connect()
        rows = list(client.stream_results('SELECT 1'))

        assert rows == [['2024-01-15 10:30:00', 'hello', 42]]
