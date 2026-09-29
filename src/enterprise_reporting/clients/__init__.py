"""
Clients used to access third party systems.
"""

import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from edx_rest_api_client.client import get_oauth_access_token

from enterprise_reporting.utils import retry_on_exception

LOGGER = logging.getLogger(__name__)


class EdxOAuth2APIMixin:
    """
    Base API Client Mixin for accessing edX IDA API endpoints.
    """
    @staticmethod
    def refresh_token(func):
        """
        Use this method decorator to ensure the JWT token is refreshed when needed.
        """
        @wraps(func)
        def inner(self, *args, **kwargs):
            """
            Before calling the wrapped function, we check if the JWT token is expired, and if so, re-connect.
            """
            if self.token_expired():
                self.connect()
            return func(self, *args, **kwargs)
        return inner


class EdxOAuth2APIClient(EdxOAuth2APIMixin):
    """
    Base API Client for accessing edX IDA API endpoints.
    """

    LMS_ROOT_URL = os.getenv('LMS_ROOT_URL', default='')
    ENTERPRISE_CATALOG_ROOT_URL = os.getenv('ENTERPRISE_CATALOG_ROOT_URL', default='https://enterprise-catalog.edx.org')
    LMS_OAUTH_HOST = os.getenv('LMS_OAUTH_HOST', default='')
    API_BASE_URL = LMS_ROOT_URL + '/api/'
    ACCESS_TOKEN_EXPIRY_THRESHOLD_IN_SECONDS = 60

    DEFAULT_VALUE_SAFEGUARD = object()

    def __init__(self, client_id=None, client_secret=None):
        """
        Connect to the REST API.
        """
        self.client_id = client_id or os.environ.get('LMS_OAUTH_KEY')
        self.client_secret = client_secret or os.environ.get('LMS_OAUTH_SECRET')
        self.expires_at = datetime.utcnow()
        self.access_token = None

    @retry_on_exception(max_retries=3, delay=2, backoff=2)
    def connect(self):
        """
        Connect to the REST API, authenticating with an access token retrieved with our client credentials.
        """
        url = urljoin(f'{self.LMS_OAUTH_HOST}/', 'oauth2/access_token')
        self.access_token, self.expires_at = get_oauth_access_token(url, self.client_id, self.client_secret)

    def token_expired(self):
        """
        Return True if the JWT token has expired, False if not.
        """
        return datetime.utcnow() > (self.expires_at - timedelta(seconds=self.ACCESS_TOKEN_EXPIRY_THRESHOLD_IN_SECONDS))

    @EdxOAuth2APIMixin.refresh_token
    def _requests(self, url, querystring):
        headers = {'Authorization': "JWT {}".format(self.access_token)}
        response = requests.get(
            url,
            headers=headers,
            params=querystring
        )
        response.raise_for_status()
        data = response.json()
        return data

    def _load_data(
            self,
            resource,
            detail_resource=None,
            resource_id=None,
            querystring=None,
            should_traverse_pagination=False,
            default=DEFAULT_VALUE_SAFEGUARD,
    ):
        """
        Loads a response from a call to one of the API endpoints.

        Arguments:
            resource: The endpoint resource name.
            detail_resource: The sub-resource to append to the path.
            resource_id: The resource ID for the specific detail to get from the endpoint.
            querystring: Optional query string parameters.
            should_traverse_pagination: Whether to traverse pagination or return paginated response.
            default: The default value to return in case of no response content.

        Returns
            (JSON): Data returned by the API.
        """
        default_val = default if default is not self.DEFAULT_VALUE_SAFEGUARD else {}
        querystring = querystring or {}
        path = resource
        if resource_id:
            path += '/' + resource_id
        if detail_resource:
            path += '/' + detail_resource

        url = urljoin(f'{self.API_BASE_URL}/', path)
        data = self._requests(url, querystring)

        if should_traverse_pagination:
            results = self.traverse_pagination(data, url)
            data = {
                'count': len(results),
                'next': None,
                'previous': None,
                'results': results,
            }

        return data or default_val

    def traverse_pagination(self, data, url):
        """
        Traverse a paginated API response.

        Extracts and concatenates "results" (list of dict) returned by DRF-powered
        APIs.

        Arguments:
            data (Dict): Current response dict from service API
            url (str): API endpoint path

        Returns:
            list of dict.
        """
        results = data.get('results', [])

        next_page = data.get('next')
        while next_page:
            querystring = parse_qs(urlparse(next_page).query, True)
            request_data = self._requests(url, querystring)

            results += request_data.get('results', [])
            next_page = request_data.get('next')

        return results
