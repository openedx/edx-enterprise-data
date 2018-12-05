"""
Clients used to connect to other systems.
"""
from __future__ import absolute_import, unicode_literals

import logging

from edx_django_utils.cache import TieredCache
from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import HttpClientError, HttpServerError
from rest_framework.exceptions import NotFound, ParseError

from django.conf import settings

from enterprise_data.utils import get_cache_key

DEFAULT_REPORTING_CACHE_TIMEOUT = 60 * 60 * 6  # 6 hours (Value is in seconds)
LOGGER = logging.getLogger('enterprise_data')


class EnterpriseApiClient(EdxRestApiClient):
    """
    The EnterpriseApiClient is used to communicate with the enterprise API endpoints in the LMS.

    This class is a sub-class of the edX Rest API Client
    (https://github.com/edx/edx-rest-api-client).
    """

    API_BASE_URL = settings.LMS_BASE_URL + 'enterprise/api/v1/'
    ENTERPRISE_DATA_API_GROUP = 'enterprise_data_api_access'

    def __init__(self, jwt):
        """
        Initialize client with given jwt.
        """
        super(EnterpriseApiClient, self).__init__(self.API_BASE_URL, jwt=jwt)

    def get_enterprise_learner(self, user):
        """
        Get an enterprise learner record for a given user with the enterprise association.

        Returns: learner record or None if unable to retrieve or no Enterprise Learner exists
        """
        try:
            querystring = {'username': user.username}
            endpoint = getattr(self, 'enterprise-learner')  # pylint: disable=literal-used-as-attribute
            response = endpoint.get(**querystring)
        except (HttpClientError, HttpServerError) as exc:
            LOGGER.warning("Unable to retrieve Enterprise Customer Learner details for user {}: {}"
                           .format(user.username, exc))
            raise exc

        if response.get('results', None) is None:
            raise NotFound('Unable to process Enterprise Customer Learner details for user {}: No Results Found'
                           .format(user.username))

        if response['count'] > 1:
            raise ParseError('Multiple Enterprise Customer Learners found for user {}'.format(user.username))

        if response['count'] == 0:
            return None

        return response['results'][0]

    def get_with_access_to(self, user, enterprise_id):
        """
        Get the enterprises that this user has access to for the data api permission django group.
        """
        cache_key = get_cache_key(
            resource='enterprise-customer',
            user=user.username,
            enterprise_customer=enterprise_id,
        )
        cached_response = TieredCache.get_cached_response(cache_key)
        if cached_response.is_found:
            return cached_response.value

        try:
            querystring = {
                'permissions': [self.ENTERPRISE_DATA_API_GROUP],
                'enterprise_id': enterprise_id,
            }
            endpoint = getattr(self, 'enterprise-customer')  # pylint: disable=literal-used-as-attribute
            endpoint = endpoint.with_access_to
            response = endpoint.get(**querystring)
        except (HttpClientError, HttpServerError) as exc:
            LOGGER.warning("Unable to retrieve Enterprise Customer with_access_to details for user {}: {}"
                           .format(user.username, exc))
            raise exc

        if response.get('results', None) is None:
            raise NotFound('Unable to process Enterprise Customer with_access_to details for user {}, enterprise {}:'
                           ' No Results Found'
                           .format(user.username, enterprise_id))

        if response['count'] > 1:
            raise ParseError('Multiple Enterprise Customers found for user {}, enterprise id {}'
                             .format(user.username, enterprise_id))

        if response['count'] == 0:
            return None

        TieredCache.set_all_tiers(cache_key, response['results'][0], DEFAULT_REPORTING_CACHE_TIMEOUT)
        return response['results'][0]
