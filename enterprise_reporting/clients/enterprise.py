# -*- coding: utf-8 -*-
"""
Client for connecting to the LMS Enterprise endpoints.
"""

from __future__ import absolute_import, unicode_literals

from enterprise_reporting.clients import EdxOAuth2APIClient, traverse_pagination


class EnterpriseAPIClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Enterprise API.
    """

    API_BASE_URL = EdxOAuth2APIClient.LMS_ROOT_URL + '/enterprise/api/v1/'
    APPEND_SLASH = True

    ENTERPRISE_REPORTING_ENDPOINT = 'enterprise_customer_reporting'

    DEFAULT_VALUE_SAFEGUARD = object()

    def get_all_enterprise_reporting_configs(self, **kwargs):
        """
        Query the enterprise customer reporting endpoint for all available configs.
        """
        return self._load_data(
            self.ENTERPRISE_REPORTING_ENDPOINT,
            should_traverse_pagination=True,
            **kwargs
        )

    def get_enterprise_reporting_config(self, enterprise_customer_id, **kwargs):
        """
        Query the enterprise customer reporting endpoint for a given enterprise customer.
        """
        return self._load_data(
            self.ENTERPRISE_REPORTING_ENDPOINT,
            querystring={'enterprise_customer': enterprise_customer_id},
            **kwargs
        )

    @EdxOAuth2APIClient.refresh_token
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
        Loads a response from a call to one of the Enterprise endpoints.

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
