"""
Test the utility functions in the admin_analytics app for data loading operations.
"""
from mock import patch

from django.test import TestCase

from enterprise_data.admin_analytics.data_loaders import fetch_max_enrollment_datetime


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
