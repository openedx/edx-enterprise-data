"""
Client for connecting to the LMS Enterprise endpoints.
"""


import logging
import os
from collections import OrderedDict
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin

from enterprise_reporting.clients import EdxOAuth2APIClient
from enterprise_reporting import utils

LOGGER = logging.getLogger(__name__)


class EnterpriseCatalogAPIClient(EdxOAuth2APIClient):
    """
    Client for connect to the Enterprise Catalog Service API.
    """
    API_BASE_URL = EdxOAuth2APIClient.ENTERPRISE_CATALOG_ROOT_URL + '/api/v1/'

    APPEND_SLASH = True
    ENTERPRISE_CATALOGS_ENDPOINT = 'enterprise-catalogs'
    GET_CONTENT_METADATA_ENDPOINT = ENTERPRISE_CATALOGS_ENDPOINT + '/{}/get_content_metadata'

    ENTERPRISE_REPORTING_ENDPOINT = 'enterprise_customer_reporting'
    ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT = 'enterprise_catalogs'

    PAGE_SIZE = os.getenv('PAGE_SIZE', default=1000)

    def traverse_get_content_metadata(self, endpoint, query, catalog_uuid):
        """
        Helper method to traverse over a paginated response from the enterprise-catalog service's `get_content_metadata`
        endpoint.
        """
        content_metadata = OrderedDict()
        try:
            response = endpoint.get(**query)
            for item in utils.traverse_pagination(response, endpoint):
                content_id = utils.get_content_metadata_item_id(item)
                # This code used to rely on the LMS enterprise API endpoints who's responses contained less data than
                # the enterprise catalog services, so we need to massage the response ie filter out new, not expected
                # fields
                item_crs = item.get('course_runs', [])
                formatted_course_runs = []
                for cr in item_crs:
                    formatted_course_run = {
                        'key': cr.get('key'),
                        'enrollment_start': cr.get('enrollment_start'),
                        'enrollment_end': cr.get('enrollment_end'),
                        'go_live_date': cr.get('go_live_date'),
                        'start': cr.get('start'),
                        'end': cr.get('end'),
                        'modified': cr.get('modified'),
                        'availability': cr.get('availability'),
                        'status': cr.get('status'),
                        'pacing_type': cr.get('pacing_type'),
                        # New endpoint uses `type` instead of enrollment mode
                        'enrollment_mode': cr.get('type'),
                        'min_effort': cr.get('min_effort'),
                        'max_effort': cr.get('max_effort'),
                        'weeks_to_complete': cr.get('weeks_to_complete'),
                        'estimated_hours': cr.get('estimated_hours'),
                        'first_enrollable_paid_seat_price': cr.get('first_enrollable_paid_seat_price'),
                        'is_enrollable': cr.get('is_enrollable'),
                    }
                    formatted_course_runs.append(formatted_course_run)

                subjects = item.get('subjects', [])
                formatted_subjects = []
                for subject in subjects:
                    subject_name = subject.get('name')
                    if subject_name:
                        formatted_subjects.append(subject_name)

                formatted_metadata = {
                    'active': item.get('active'),
                    'aggregation_key': item.get('aggregation_key'),
                    'card_image_url': item.get('card_image_url'),
                    'content_type': item.get('content_type'),
                    'course_ends': item.get('course_ends'),
                    'course_runs': formatted_course_runs,
                    'end_date': item.get('end_date'),
                    'enrollment_url': item.get('enrollment_url'),
                    'full_description': item.get('full_description'),
                    'image_url': item.get('image_url'),
                    'key': item.get('key'),
                    'languages': item.get('languages'),
                    'organizations': item.get('organizations'),
                    'seat_types': item.get('seat_types'),
                    'short_description': item.get('short_description'),
                    'skill_names': item.get('skill_names'),
                    'skills': item.get('skills'),
                    'subjects': formatted_subjects,
                    'title': item.get('title'),
                    'uuid': item.get('uuid'),
                }
                content_metadata[content_id] = formatted_metadata
        except (ConnectionError, Timeout):
            LOGGER.exception(
                f'Failed to get content metadata for Catalog {catalog_uuid} in enterprise-catalog',
                exc_info=True,
            )
            raise

        return content_metadata

    @EdxOAuth2APIClient.refresh_token
    def get_content_metadata(self, enterprise_customer_catalogs):
        """Return all content metadata contained in the catalogs associated with a reporting config."""
        content_metadata = OrderedDict()
        for catalog in enterprise_customer_catalogs.get('results', []):
            endpoint = getattr(self.client, self.GET_CONTENT_METADATA_ENDPOINT.format(catalog['uuid']))
            query = {'page_size': self.PAGE_SIZE}
            traversed_metadata = self.traverse_get_content_metadata(endpoint, query, catalog['uuid'])
            content_metadata.update(traversed_metadata)

        # We only made this a dictionary to help filter out duplicates by a common key. We just want values now.
        return list(content_metadata.values())


class EnterpriseAPIClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Enterprise API.
    """

    API_BASE_URL = EdxOAuth2APIClient.LMS_ROOT_URL + '/enterprise/api/v1/'
    APPEND_SLASH = True

    ENTERPRISE_REPORTING_ENDPOINT = 'enterprise_customer_reporting'
    ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT = 'enterprise_catalogs'

    PAGE_SIZE = os.getenv('PAGE_SIZE', default=1000)

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
    def get_content_metadata(self, enterprise_customer_uuid, reporting_config):
        """Return all content metadata contained in the catalogs associated with an Enterprise Customer."""
        content_metadata = OrderedDict()

        enterprise_customer_catalogs = utils.extract_catalog_uuids_from_reporting_config(reporting_config)
        if not enterprise_customer_catalogs.get('results'):
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
        return list(content_metadata.values())

    @EdxOAuth2APIClient.refresh_token
    def get_customer_catalogs(self, enterprise_customer_uuid):
        """Return all catalog uuids owned by an Enterprise Customer."""
        return self._load_data(
            self.ENTERPRISE_CUSTOMER_CATALOGS_ENDPOINT,
            should_traverse_pagination=True,
            querystring={
                'enterprise_customer': enterprise_customer_uuid,
                'page_size': self.PAGE_SIZE,
            },
        )


class EnterpriseDataApiClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Enterprise Data API.
    """

    API_BASE_URL = os.getenv('ANALYTICS_API_URL', default='') + '/enterprise/api/v0'
    APPEND_SLASH = True

    PAGE_SIZE = os.getenv('PAGE_SIZE', default=1000)

    @EdxOAuth2APIClient.refresh_token
    def get_enterprise_enrollments(self, enterprise_customer_uuid):
        return self._load_data(
            'enterprise',
            resource_id=enterprise_customer_uuid,
            detail_resource='enrollments',
            should_traverse_pagination=True,
            querystring={'page_size': self.PAGE_SIZE},
        )


class EnterpriseDataV1ApiClient(EnterpriseDataApiClient):
    """
    Client for connecting to the Enterprise Data V1 API.
    """

    API_BASE_URL = os.getenv('ANALYTICS_API_URL', default='') + '/enterprise/api/v1'


class AnalyticsDataApiClient(EdxOAuth2APIClient):
    """
    Client for connecting to the Analytics Data API.
    """

    API_BASE_URL = os.getenv('ANALYTICS_API_URL', default='') + '/api/v0'
    APPEND_SLASH = True

    PAGE_SIZE = os.getenv('PAGE_SIZE', default=1000)

    @EdxOAuth2APIClient.refresh_token
    def get_enterprise_engagements(self, enterprise_customer_uuid):
        return self._load_data(
            'enterprise',
            resource_id=enterprise_customer_uuid,
            detail_resource='engagements',
            should_traverse_pagination=True,
            querystring={'page_size': self.PAGE_SIZE},
        )
