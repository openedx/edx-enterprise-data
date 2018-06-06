# -*- coding: utf-8 -*-
"""
Client for connecting to the LMS Enterprise endpoints.
"""

from __future__ import absolute_import, unicode_literals

import os
from collections import OrderedDict

from enterprise_reporting.clients import EdxOAuth2APIClient


class EnterpriseAPIClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Enterprise API.
    """

    API_BASE_URL = EdxOAuth2APIClient.LMS_ROOT_URL + '/enterprise/api/v1/'
    APPEND_SLASH = True

    ENTERPRISE_REPORTING_ENDPOINT = 'enterprise_customer_reporting'
    ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT = 'enterprise_catalogs'

    PAGE_SIZE = os.environ.get('PAGE_SIZE', default=1000)

    @EdxOAuth2APIClient.refresh_token
    def get_all_enterprise_reporting_configs(self, **kwargs):
        """
        Query the enterprise customer reporting endpoint for all available configs.
        """
        return self._load_data(
            self.ENTERPRISE_REPORTING_ENDPOINT,
            should_traverse_pagination=True,
            **kwargs
        )

    @EdxOAuth2APIClient.refresh_token
    def get_enterprise_reporting_configs(self, enterprise_customer_uuid, **kwargs):
        """
        Query the enterprise customer reporting endpoint for a given enterprise customer.
        """
        return self._load_data(
            self.ENTERPRISE_REPORTING_ENDPOINT,
            querystring={'enterprise_customer': enterprise_customer_uuid},
            should_traverse_pagination=True,
            **kwargs
        )

    @EdxOAuth2APIClient.refresh_token
    def get_content_metadata(self, enterprise_customer_uuid):
        """Return all content metadata contained in the catalogs associated with an Enterprise Customer."""
        content_metadata = OrderedDict()
        enterprise_customer_catalogs = self._load_data(
            self.ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT,
            should_traverse_pagination=True,
            querystring={
                'enterprise_customer': enterprise_customer_uuid,
                'page_size': self.PAGE_SIZE,
            },
        )
        for catalog in enterprise_customer_catalogs.get('results', []):
            catalog_content = self._load_data(
                self.ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT,
                resource_id=catalog['uuid'],
                should_traverse_pagination=True,
                querystring={'page_size': self.PAGE_SIZE},
            )
            # It's possible that there are duplicate items.
            # Filter them out by assigning common items to their common identifier in a dictionary.
            for item in catalog_content['results']:
                key = 'uuid' if item['content_type'] == 'program' else 'key'
                content_metadata[item[key]] = item

        # We only made this a dictionary to help filter out duplicates by a common key. We just want values now.
        return content_metadata.values()


class EnterpriseDataApiClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Enterprise Data API.
    """

    API_BASE_URL = os.environ.get('ANALYTICS_API_URL') + '/enterprise/api/v0'
    APPEND_SLASH = True

    PAGE_SIZE = os.environ.get('PAGE_SIZE', default=1000)

    @EdxOAuth2APIClient.refresh_token
    def get_enterprise_enrollments(self, enterprise_customer_uuid):
        return self._load_data(
            'enterprise',
            resource_id=enterprise_customer_uuid,
            detail_resource='enrollments',
            should_traverse_pagination=True,
            querystring={'page_size': self.PAGE_SIZE},
        )
