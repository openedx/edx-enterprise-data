"""
Clients used to connect to other systems.
"""


import logging
from urllib.parse import urljoin

from edx_django_utils.cache import TieredCache
from edx_rest_api_client.client import OAuthAPIClient
from requests.exceptions import HTTPError, RequestException
from rest_framework.exceptions import NotFound, ParseError

from django.conf import settings

from enterprise_data.utils import get_cache_key, update_session_with_enterprise_data

DEFAULT_REPORTING_CACHE_TIMEOUT = 60 * 60 * 6  # 6 hours (Value is in seconds)
LOGGER = logging.getLogger('enterprise_data')


class EnterpriseApiClient(OAuthAPIClient):
    """
    The EnterpriseApiClient is used to communicate with the enterprise API endpoints in the LMS.

    This class is a sub-class of the OAuthAPIClient
    (https://github.com/openedx/edx-rest-api-client).
    """

    API_BASE_URL = urljoin(settings.LMS_BASE_URL + '/', 'enterprise/api/v1/')

    def get_enterprise_learner(self, user):
        """
        Get an enterprise learner record for a given user with the enterprise association.

        Returns: learner record or None if unable to retrieve or no Enterprise Learner exists
        """
        try:
            querystring = {'username': user.username}
            url = urljoin(self.API_BASE_URL, 'enterprise-learner')
            response = self.get(url, params=querystring)
            response.raise_for_status()
            data = response.json()
        except (HTTPError, RequestException) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Customer Learner details. "
                f"User: {user.username}, Exception: {exc}"
            )
            raise

        if data.get('results', None) is None:
            LOGGER.warning(
                f"[Data Overview Failure] Enterprise Customer Learner details could not be found. User: {user.username}"
            )
            raise NotFound('Unable to process Enterprise Customer Learner details for user {}: No Results Found'
                           .format(user.username))

        if data['count'] > 1:
            LOGGER.warning(
                f"[Data Overview Failure] Multiple Enterprise Customer Learners found. User: {user.username}"
            )
            raise ParseError(f'Multiple Enterprise Customer Learners found for user {user.username}')

        if data['count'] == 0:
            return None

        return data['results'][0]

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

        url = urljoin(self.API_BASE_URL, 'enterprise-customer')

        try:
            response = self.get(url)
            response.raise_for_status()
            data = response.json()
        except (HTTPError, RequestException) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Customer details. "
                f"User: {user.username}, Enterprise: {enterprise_id}, Exception: {exc}"
            )
            raise

        TieredCache.set_all_tiers(cache_key, data, DEFAULT_REPORTING_CACHE_TIMEOUT)

        return data

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
