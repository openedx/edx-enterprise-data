"""
Tests for `./manage.py pre_warm_analytics_cache` management command.
"""
from datetime import datetime
from unittest import TestCase

from mock import MagicMock, patch
from pytest import mark

from django.core.management import call_command


@mark.django_db
class Test(TestCase):
    """
    Tests to validate the behavior of `./manage.py pre_warm_analytics_cache` management command.
    """
    def setUp(self):
        """
        Setup method.
        """
        super().setUp()
        self.enterprise_uuid = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'

        get_enrollment_date_range_patcher = patch(
            'enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_enrollment_date_range',
            return_value=(datetime.now(), datetime.now())
        )

        get_enrollment_date_range_patcher.start()
        self.addCleanup(get_enrollment_date_range_patcher.stop)

    @patch(
        'enterprise_data.admin_analytics.database.tables.fact_engagement_admin_dash.run_query',
        MagicMock(return_value=[])
    )
    @patch(
        'enterprise_data.admin_analytics.database.tables.fact_enrollment_admin_dash.run_query',
        MagicMock(return_value=[])
    )
    @patch(
        'enterprise_data.admin_analytics.database.tables.skills_daily_rollup_admin_dash.run_query',
        MagicMock(return_value=[])
    )
    @patch('enterprise_data.api.v1.views.analytics_enrollments.FactEnrollmentAdminDashTable.get_top_enterprises')
    @patch('enterprise_data.cache.decorators.cache.set')
    @patch('enterprise_data.cache.decorators.cache.get')
    def test_pre_warm_analytics_cache(self, mock_get_cache, mock_set_cache, mock_get_top_enterprises):
        """
        Validate that the command caches the analytics data for a large enterprise.
        """
        mock_get_top_enterprises.return_value = [
            self.enterprise_uuid
        ]
        mock_get_cache.return_value = MagicMock(is_found=False)

        call_command('pre_warm_analytics_cache')

        assert mock_get_cache.call_count == 23
        assert mock_set_cache.call_count == 23
