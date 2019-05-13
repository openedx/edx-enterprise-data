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

from enterprise_data.utils import get_cache_key, update_session_with_enterprise_data

DEFAULT_REPORTING_CACHE_TIMEOUT = 60 * 60 * 6  # 6 hours (Value is in seconds)
LOGGER = logging.getLogger('enterprise_data')


class EnterpriseApiClient(EdxRestApiClient):
    """
    The EnterpriseApiClient is used to communicate with the enterprise API endpoints in the LMS.

    This class is a sub-class of the edX Rest API Client
    (https://github.com/edx/edx-rest-api-client).
    """

    API_BASE_URL = settings.LMS_BASE_URL + 'enterprise/api/v1/'

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

    def get_enterprise_customer(self, user, enterprise_id):
        """
        Get the enterprises that this user has access to.
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
            endpoint = getattr(self, 'enterprise-customer')  # pylint: disable=literal-used-as-attribute
            endpoint = endpoint(enterprise_id)
            response = endpoint.get()
        except (HttpClientError, HttpServerError) as exc:
            LOGGER.warning("Unable to retrieve Enterprise Customer details for user {}: {}"
                           .format(user.username, exc))
            raise exc

        TieredCache.set_all_tiers(cache_key, response, DEFAULT_REPORTING_CACHE_TIMEOUT)

        return response

    def get_enterprise_and_update_session(self, request):
        """
        Get the enterprise customer data and updates the session.

        Returns:
            Enterprise Customer or None if unable to get enterprise information
        """
        enterprise_id = request.parser_context.get('kwargs', {}).get('enterprise_id', '')
        session = request.session
        enterprise_data = None

        audit_enrollment_check = enterprise_id not in session.get('enable_audit_enrollment', {})
        data_sharing_consent_check = enterprise_id not in session.get('enforce_data_sharing_consent', {})

        if audit_enrollment_check or data_sharing_consent_check:
            enterprise_data = self.get_enterprise_customer(request.user, enterprise_id)
            enable_audit_enrollment = False
            enforce_data_sharing_consent = False

            if enterprise_data:
                enable_audit_enrollment = enterprise_data.get('enable_audit_enrollment', False)
                enforce_data_sharing_consent = enterprise_data.get('enforce_data_sharing_consent', '')

            update_session_with_enterprise_data(
                request,
                enterprise_id,
                enable_audit_enrollment=enable_audit_enrollment,
                enforce_data_sharing_consent=enforce_data_sharing_consent,
            )

        return enterprise_data
