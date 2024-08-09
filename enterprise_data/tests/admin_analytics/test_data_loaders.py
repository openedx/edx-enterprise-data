"""
Test the utility functions in the admin_analytics app for data loading operations.
"""
from uuid import uuid4

import pytest
from mock import patch

from django.http import Http404
from django.test import TestCase

from enterprise_data.admin_analytics.data_loaders import (
    fetch_engagement_data,
    fetch_enrollment_data,
    fetch_max_enrollment_datetime,
    fetch_skills_data,
)
from enterprise_data.tests.test_utils import (
    get_dummy_engagements_data,
    get_dummy_enrollments_data,
    get_dummy_skills_data,
)


class TestDataLoaders(TestCase):
    """
    Test suite for the utility functions in the admin_analytics package for data loading operations.
    """

    def test_fetch_max_enrollment_datetime(self):
        """
        Validate the fetch_max_enrollment_datetime function.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            mock_run_query.return_value = [['2024-07-26']]

            max_enrollment_date = fetch_max_enrollment_datetime()
            self.assertEqual(max_enrollment_date.strftime('%Y-%m-%d'), '2024-07-26')

            # Validate the case where the query returns an empty result.
            mock_run_query.return_value = []
            max_enrollment_date = fetch_max_enrollment_datetime()
            self.assertIsNone(max_enrollment_date)

    def test_fetch_engagement_data(self):
        """
        Validate the fetch_engagement_data function.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            enterprise_uuid = str(uuid4())
            mock_run_query.return_value = [
                list(item.values()) for item in get_dummy_engagements_data(enterprise_uuid, 10)
            ]

            engagement_data = fetch_engagement_data(enterprise_uuid)
            self.assertEqual(engagement_data.shape, (10, 14))

    def test_fetch_engagement_data_empty_data(self):
        """
        Validate the fetch_engagement_data function behavior when no data is returned from the query.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            mock_run_query.return_value = []
            enterprise_uuid = str(uuid4())
            with pytest.raises(Http404) as error:
                fetch_engagement_data(enterprise_uuid)
            error.value.message = f'No engagement data found for enterprise {enterprise_uuid}'

    def test_fetch_enrollment_data(self):
        """
        Validate the fetch_enrollment_data function.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            enterprise_uuid = str(uuid4())
            mock_run_query.return_value = [
                list(item.values()) for item in get_dummy_enrollments_data(enterprise_uuid)
            ]

            enrollment_data = fetch_enrollment_data(enterprise_uuid)
            self.assertEqual(enrollment_data.shape, (10, 21))

    def test_fetch_enrollment_data_empty_data(self):
        """
        Validate the fetch_enrollment_data function behavior when no data is returned from the query.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            mock_run_query.return_value = []
            enterprise_uuid = str(uuid4())
            with pytest.raises(Http404) as error:
                fetch_enrollment_data(enterprise_uuid)
            error.value.message = f'No enrollment data found for enterprise {enterprise_uuid}'

    def test_fetch_skills_data(self):
        """
        Validate the fetch_skills_data function.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            enterprise_uuid = str(uuid4())
            mock_run_query.return_value = [
                list(item.values()) for item in get_dummy_skills_data(enterprise_uuid)
            ]

            skills_data = fetch_skills_data(enterprise_uuid)
            self.assertEqual(skills_data.shape, (10, 15))

    def test_fetch_skills_data_empty_data(self):
        """
        Validate the fetch_skills_data function behavior when no data is returned from the query.
        """
        with patch('enterprise_data.admin_analytics.data_loaders.run_query') as mock_run_query:
            mock_run_query.return_value = []
            enterprise_uuid = str(uuid4())
            with pytest.raises(Http404) as error:
                fetch_skills_data(enterprise_uuid)
            error.value.message = f'No skills data found for enterprise {enterprise_uuid}'
