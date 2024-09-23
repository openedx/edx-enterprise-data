"""
Test the utility functions in the admin_analytics app.
"""
from datetime import datetime, timedelta

from mock import patch

from django.test import TestCase

from enterprise_data.admin_analytics.utils import (
    fetch_and_cache_engagements_data,
    fetch_and_cache_enrollments_data,
    get_cache_timeout,
)


class TestUtils(TestCase):
    """
    Test suite for the utility functions in the admin_analytics package.
    """

    def test_get_cache_timeout(self):
        """
        Validate the get_cache_timeout function.
        """
        now = datetime.now().replace(microsecond=0)
        with patch('enterprise_data.admin_analytics.utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            cache_expiry = now
            self.assertEqual(get_cache_timeout(cache_expiry), 0)

            cache_expiry = now + timedelta(seconds=10)
            self.assertEqual(get_cache_timeout(cache_expiry), 10)

            cache_expiry = now + timedelta(seconds=100)
            self.assertEqual(get_cache_timeout(cache_expiry), 100)

            # Validate the case where cache_expiry is in the past.
            cache_expiry = now - timedelta(seconds=10)
            self.assertEqual(get_cache_timeout(cache_expiry), 0)

    def test_fetch_and_cache_enrollments_data(self):
        """
        Validate the fetch_and_cache_enrollments_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_enrollment_data') as mock_fetch_enrollment_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is not found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = False
                mock_fetch_enrollment_data.return_value = 'enrollments'

                enrollments = fetch_and_cache_enrollments_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(enrollments, 'enrollments')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 1)

    def test_fetch_and_cache_enrollments_data_with_data_cache_found(self):
        """
        Validate the fetch_and_cache_enrollments_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_enrollment_data') as mock_fetch_enrollment_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = True
                mock_tiered_cache.get_cached_response.return_value.value = 'cached-enrollments'
                mock_fetch_enrollment_data.return_value = 'enrollments'

                enrollments = fetch_and_cache_enrollments_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(enrollments, 'cached-enrollments')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 0)

    def test_fetch_and_cache_engagements_data(self):
        """
        Validate the fetch_and_cache_engagements_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_engagement_data') as mock_fetch_engagement_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is not found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = False
                mock_fetch_engagement_data.return_value = 'engagements'

                enrollments = fetch_and_cache_engagements_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(enrollments, 'engagements')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 1)

    def test_fetch_and_cache_engagements_data_with_data_cache_found(self):
        """
        Validate the fetch_and_cache_engagements_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_engagement_data') as mock_fetch_engagement_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = True
                mock_tiered_cache.get_cached_response.return_value.value = 'cached-engagements'
                mock_fetch_engagement_data.return_value = 'engagements'

                enrollments = fetch_and_cache_engagements_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(enrollments, 'cached-engagements')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 0)
