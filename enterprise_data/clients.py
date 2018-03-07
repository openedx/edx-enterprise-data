"""
Clients used to connect to other systems.
"""
from __future__ import absolute_import, unicode_literals

import logging

from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import HttpClientError, HttpServerError
from rest_framework.exceptions import NotFound, ParseError

from django.conf import settings

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
            endpoint = getattr(self, 'enterprise-learner')
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
