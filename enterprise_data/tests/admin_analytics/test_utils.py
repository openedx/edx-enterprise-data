"""
Test the utility functions in the admin_analytics app.
"""
from datetime import datetime, timedelta

import pandas
from mock import patch

from django.test import TestCase

from enterprise_data.admin_analytics.utils import (
    fetch_and_cache_engagements_data,
    fetch_and_cache_enrollments_data,
    fetch_and_cache_skills_data,
    get_cache_timeout,
    get_skills_bubble_chart_df,
    get_top_skills_completion,
    get_top_skills_enrollment,
)
from enterprise_data.utils import date_filter


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

    def test_fetch_and_cache_skills_data(self):
        """
        Validate the fetch_and_cache_skills_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_skills_data') as mock_fetch_skills_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is not found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = False
                mock_fetch_skills_data.return_value = 'skills'
                skills = fetch_and_cache_skills_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(skills, 'skills')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 1)

    def test_fetch_and_cache_skills_data_with_data_cache_found(self):
        """
        Validate the fetch_and_cache_skills_data function.
        """
        with patch('enterprise_data.admin_analytics.utils.fetch_skills_data') as mock_fetch_skills_data:
            with patch('enterprise_data.admin_analytics.utils.TieredCache') as mock_tiered_cache:
                # Simulate the scenario where the data is found in the cache.
                mock_tiered_cache.get_cached_response.return_value.is_found = True
                mock_tiered_cache.get_cached_response.return_value.value = 'cached-skills'
                mock_fetch_skills_data.return_value = 'skills'

                skills = fetch_and_cache_skills_data('enterprise_id', datetime.now() + timedelta(seconds=10))
                self.assertEqual(skills, 'cached-skills')
                self.assertEqual(mock_tiered_cache.get_cached_response.call_count, 1)
                self.assertEqual(mock_tiered_cache.set_all_tiers.call_count, 0)

    def test_get_skills_bubble_chart_df(self):
        """
        Validate the get_skills_bubble_chart_df function.
        """
        # Mock skills data
        skills = pandas.DataFrame({
            'skill_name': ['Skill A', 'Skill B', 'Skill C'],
            'skill_type': ['Type 1', 'Type 2', 'Type 1'],
            'enrolls': [100, 200, 150],
            'completions': [50, 100, 75],
            'date': [datetime.now(), datetime.now(), datetime.now()],
        })

        # Define the expected result
        expected_result = pandas.DataFrame({
            'skill_name': ['Skill B', 'Skill C', 'Skill A'],
            'skill_type': ['Type 2', 'Type 1', 'Type 1'],
            'enrolls': [200, 150, 100],
            'completions': [100, 75, 50]
        })
        # Reset the index for the expected result
        expected_result = expected_result.reset_index(drop=True)

        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now()
        filtered_skills = date_filter(start_date, end_date, skills, 'date')
        # Call the function
        result = get_skills_bubble_chart_df(filtered_skills)

        # Reset the index for the result
        result = result.reset_index(drop=True)

        # Assert the result
        pandas.testing.assert_frame_equal(result, expected_result)

    def test_get_top_skills_enrollment(self):
        """
        Validate the get_top_skills_enrollment function.
        """
        # Mock skills data
        skills = pandas.DataFrame({
            'primary_subject_name': ['engineering', 'communication', 'engineering', 'other'],
            'skill_name': ['Skill A', 'Skill B', 'Skill A', 'Skill D'],
            'enrolls': [100, 200, 150, 300],
            'completions': [50, 100, 75, 150],
            'date': [datetime.now(), datetime.now(), datetime.now(), datetime.now()],
        })

        # Define the expected result
        expected_result = pandas.DataFrame({
            'skill_name': ['Skill B', 'Skill A', 'Skill D'],
            'primary_subject_name': ['communication', 'engineering', 'other'],
            'count': [200, 250, 300]
        })
        # Reset the index for the expected result
        expected_result = expected_result.reset_index(drop=True)
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now()
        filtered_skills = date_filter(start_date, end_date, skills, 'date')

        # Call the function
        result = get_top_skills_enrollment(filtered_skills)

        # Reset the index for the result
        result = result.reset_index(drop=True)

        # Assert the result
        pandas.testing.assert_frame_equal(result, expected_result)

    def test_get_top_skills_completion(self):
        """
        Validate the get_top_skills_completion function.
        """
        # Mock skills data
        skills = pandas.DataFrame({
            'skill_name': ['Skill A', 'Skill B', 'Skill C', 'Skill D'],
            'primary_subject_name': ['communication', 'engineering', 'communication', 'other'],
            'enrolls': [100, 200, 150, 300],
            'completions': [50, 100, 75, 150],
            'date': [datetime.now(), datetime.now(), datetime.now(), datetime.now()]
        })

        # Define the expected result
        expected_result = pandas.DataFrame({
            'skill_name': ['Skill A', 'Skill C', 'Skill B', 'Skill D'],
            'primary_subject_name': ['communication', 'communication', 'engineering', 'other'],
            'count': [50, 75, 100, 150]
        })
        # Reset the index for the expected result
        expected_result = expected_result.reset_index(drop=True)
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now()
        filtered_skills = date_filter(start_date, end_date, skills, 'date')

        # Call the function
        result = get_top_skills_completion(filtered_skills)

        # Reset the index for the result
        result = result.reset_index(drop=True)

        # Assert the result
        pandas.testing.assert_frame_equal(result, expected_result)
