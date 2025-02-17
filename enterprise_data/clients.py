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

from enterprise_data.utils import get_cache_key

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

    def get_enterprise_customer(self, enterprise_uuid):
        """
        Get the enterprises that this user has access to.
        """
        LOGGER.info(f'[EnterpriseApiClient] getting latest info for enterprise customer:{enterprise_uuid}')
        cache_key = get_cache_key(
            resource='enterprise-customer',
            enterprise_customer=enterprise_uuid,
        )
        cached_response = TieredCache.get_cached_response(cache_key)
        if cached_response.is_found:
            LOGGER.info(
                f'[EnterpriseApiClient] cache info found for enterprise customer:{enterprise_uuid}'
                f' with {cached_response.value}'
            )
            return cached_response.value

        LOGGER.info(f'[EnterpriseApiClient] No cached info found for enterprise customer:{enterprise_uuid}')
        url = urljoin(self.API_BASE_URL, f'enterprise-customer/{enterprise_uuid}')

        try:
            response = self.get(url)
            response.raise_for_status()
            data = response.json()
        except (HTTPError, RequestException) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Customer details. "
                f"Enterprise: {enterprise_uuid}, Exception: {exc}"
            )
            raise

        LOGGER.info(f'[EnterpriseApiClient] Setting cached for enterprise customer:{enterprise_uuid} with {data}')
        TieredCache.set_all_tiers(cache_key, data, DEFAULT_REPORTING_CACHE_TIMEOUT)

        return data

    def get_enterprise_group_learners(self, group_uuid):
        """
        Get the learners associated with a given enterprise group.

        Returns: list of learners or None if unable to retrieve or no learners exist
        """
        LOGGER.info(f'[EnterpriseApiClient] getting learners for enterprise group:{group_uuid}')
        url = urljoin(self.API_BASE_URL, f'enterprise-group/{group_uuid}/learners/')
        all_learners = []

        try:
            while url:
                response = self.get(url)
                response.raise_for_status()
                data = response.json()
                all_learners.extend(data.get('results', []))
                url = data.get('next')  # Get the URL for the next page, if any

        except (HTTPError, RequestException) as exc:
            LOGGER.warning(
                "[Data Overview Failure] Unable to retrieve Enterprise Group Learners details. "
                f"Group: {group_uuid}, Exception: {exc}"
            )
            return None

        return all_learners
