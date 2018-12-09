# -*- coding: utf-8 -*-
"""
Clients used to access third party systems.
"""

from __future__ import absolute_import, unicode_literals

import os
from datetime import datetime
from functools import wraps
from six.moves import urllib

from edx_rest_api_client.client import EdxRestApiClient


class EdxOAuth2APIClient(object):
    """
    Base API Client for accessing edX IDA API endpoints.
    """

    LMS_ROOT_URL = os.getenv('LMS_ROOT_URL', default='')
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
        self.client = None

    def connect(self):
        """
        Connect to the REST API, authenticating with an access token retrieved with our client credentials.
        """
        access_token, expires_at = EdxRestApiClient.get_oauth_access_token(
            self.LMS_OAUTH_HOST + '/oauth2/access_token',
            self.client_id,
            self.client_secret,
            'jwt'
        )
        self.client = EdxRestApiClient(
            self.API_BASE_URL, append_slash=self.APPEND_SLASH, jwt=access_token,
        )
        self.expires_at = expires_at

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

        endpoint = getattr(self.client, resource)
        endpoint = getattr(self.client, resource)(resource_id) if resource_id else endpoint
        endpoint = getattr(endpoint, detail_resource) if detail_resource else endpoint
        response = endpoint.get(**querystring)
        if should_traverse_pagination:
            results = traverse_pagination(response, endpoint)
            response = {
                'count': len(results),
                'next': None,
                'previous': None,
                'results': results,
            }

        return response or default_val


def traverse_pagination(response, endpoint):
    """
    Traverse a paginated API response.

    Extracts and concatenates "results" (list of dict) returned by DRF-powered
    APIs.

    Arguments:
        response (Dict): Current response dict from service API
        endpoint (slumber Resource object): slumber Resource object from edx-rest-api-client

    Returns:
        list of dict.

    """
    results = response.get('results', [])

    next_page = response.get('next')
    while next_page:
        querystring = urllib.parse.parse_qs(urllib.parse.urlparse(next_page).query, True)
        response = endpoint.get(**querystring)
        results += response.get('results', [])
        next_page = response.get('next')

    return results
