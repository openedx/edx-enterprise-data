"""
Clients used to connect to other systems.
"""


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
        # If jwt token in request is already encoded into bytes decode it to avoid double encoding downstream
        jwt = jwt.decode() if isinstance(jwt, bytes) else jwt
        super().__init__(self.API_BASE_URL, jwt=jwt)

    def get_enterprise_learner(self, user):
        """
        Get an enterprise learner record for a given user with the enterprise association.

        Returns: learner record or None if unable to retrieve or no Enterprise Learner exists
        """
        try:
            querystring = {'username': user.username}
            endpoint = getattr(self, 'enterprise-learner')
            response = endpoint.get(**querystring)
        except (HttpClientError, HttpServerError) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Customer Learner details. "
                f"User: {user.username}, Exception: {exc}"
            )
            raise exc

        if response.get('results', None) is None:
            LOGGER.warning(
                f"[Data Overview Failure] Enterprise Customer Learner details could not be found. User: {user.username}"
            )
            raise NotFound('Unable to process Enterprise Customer Learner details for user {}: No Results Found'
                           .format(user.username))

        if response['count'] > 1:
            LOGGER.warning(
                f"[Data Overview Failure] Multiple Enterprise Customer Learners found. User: {user.username}"
            )
            raise ParseError(f'Multiple Enterprise Customer Learners found for user {user.username}')

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
            endpoint = getattr(self, 'enterprise-customer')
            endpoint = endpoint(enterprise_id)
            response = endpoint.get()
        except (HttpClientError, HttpServerError) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Customer details. "
                f"User: {user.username}, Enterprise: {enterprise_id}, Exception: {exc}"
            )
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

        audit_enrollment_check = enterprise_id not in session.get('enable_audit_data_reporting', {})
        data_sharing_consent_check = enterprise_id not in session.get('enforce_data_sharing_consent', {})

        if audit_enrollment_check or data_sharing_consent_check:
            enterprise_data = self.get_enterprise_customer(request.user, enterprise_id)
            enable_audit_data_reporting = False
            enforce_data_sharing_consent = False

            if enterprise_data:
                enable_audit_data_reporting = enterprise_data.get('enable_audit_data_reporting', False)
                enforce_data_sharing_consent = enterprise_data.get('enforce_data_sharing_consent', '')

            update_session_with_enterprise_data(
                request,
                enterprise_id,
                enable_audit_data_reporting=enable_audit_data_reporting,
                enforce_data_sharing_consent=enforce_data_sharing_consent,
            )

        return enterprise_data
