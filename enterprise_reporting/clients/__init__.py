"""
Clients used to access third party systems.
"""

import os
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs, urljoin, urlparse

import requests


class EdxOAuth2APIClient:
    """
    Base API Client for accessing edX IDA API endpoints.
    """

    LMS_ROOT_URL = os.getenv('LMS_ROOT_URL', default='')
    ENTERPRISE_CATALOG_ROOT_URL = os.getenv('ENTERPRISE_CATALOG_ROOT_URL', default='https://enterprise-catalog.edx.org')
    LMS_OAUTH_HOST = os.getenv('LMS_OAUTH_HOST', default='')
    API_BASE_URL = LMS_ROOT_URL + '/api/'
    APPEND_SLASH = False

    DEFAULT_VALUE_SAFEGUARD = object()

    def __init__(self, client_id=None, client_secret=None):
        """
        Connect to the REST API.
        """
        self.client_id = client_id or os.environ.get('LMS_OAUTH_KEY')
        self.client_secret = client_secret or os.environ.get('LMS_OAUTH_SECRET')
        self.expires_at = datetime.utcnow()

    def connect(self):
        """
        Connect to the REST API, authenticating with an access token retrieved with our client credentials.
        """
        response = requests.post(
            urljoin(f'{self.LMS_OAUTH_HOST}/', 'oauth2/access_token'),
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'token_type': 'jwt',
            },
            headers={
                'User-Agent': 'enterprise_reporting',
            },
            timeout=(3.1, 5)
        )
        data = response.json()
        self.access_token = data['access_token']
        self.expires_at = data['expires_in']

    def token_expired(self):
        """
        Return True if the JWT token has expired, False if not.
        """
        return datetime.utcnow() > self.expires_at

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
        path = f"{resource}{'/' + resource_id if resource_id else ''}{'/' + detail_resource if detail_resource else ''}"
        url = urljoin(f'{self.API_BASE_URL}/', path)
        headers = {'Authorization': "JWT {}".format(self.access_token)}
        response = requests.get(
            url,
            headers=headers,
            params=querystring
        )
        response.raise_for_status()
        data = response.json()

        if should_traverse_pagination:
            results = traverse_pagination(data, self.access_token, url)
            data = {
                'count': len(results),
                'next': None,
                'previous': None,
                'results': results,
            }

        return data or default_val


def traverse_pagination(response, access_token, url):
    """
    Traverse a paginated API response.

    Extracts and concatenates "results" (list of dict) returned by DRF-powered
    APIs.

    Arguments:
        response (Dict): Current response dict from service API
        access_token (str): jwt token
        url (str): API endpoint path

    Returns:
        list of dict.

    """
    results = response.get('results', [])

    next_page = response.get('next')
    while next_page:
        querystring = parse_qs(urlparse(next_page).query, True)
        headers = {'Authorization': "JWT {}".format(access_token)}
        response = requests.get(
            url,
            headers=headers,
            params=querystring
        ).json
        response.raise_for_status()
        data = response.json()
        results += data.get('results', [])
        next_page = data.get('next')

    return results
