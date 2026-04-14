"""Tests for ``SnowflakeCourseProgressSource``."""
# pylint: disable=protected-access

from unittest.mock import MagicMock, patch

import pytest

from enterprise_data.api.v1.views.lpr_data_source_snowflake import SnowflakeCourseProgressSource

ENTERPRISE_UUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
NORMALIZED_UUID = 'a1b2c3d4e5f67890abcdef1234567890'
DEFAULT_TABLE = 'PROD.ENTERPRISE.LEARNER_PROGRESS_REPORT_INTERNAL'


def _source():
    """Return a source instance under test."""
    return SnowflakeCourseProgressSource()


def _mock_ctx_and_cursor(fetchall=None):
    """Return mocked Snowflake connection and cursor objects."""
    cursor = MagicMock()
    cursor.fetchall.return_value = fetchall or []
    ctx = MagicMock()
    ctx.cursor.return_value = cursor
    return ctx, cursor


class TestInternalTable:
    """Tests for fully-qualified internal table resolution."""

    def test_default_internal_table(self):
        assert SnowflakeCourseProgressSource._internal_table() == DEFAULT_TABLE

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_custom_internal_table(self, mock_settings):
        mock_settings.LPR_SNOWFLAKE_DATABASE = 'STAGING'
        mock_settings.LPR_SNOWFLAKE_SCHEMA = 'REPORTING'
        mock_settings.LPR_SNOWFLAKE_INTERNAL_TABLE = 'COURSE_PROGRESS'
        assert SnowflakeCourseProgressSource._internal_table() == 'STAGING.REPORTING.COURSE_PROGRESS'


class TestGetConnection:
    """Tests for Snowflake connection kwargs construction."""

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.snowflake.connector')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_connection_uses_required_credentials(self, mock_settings, mock_connector):
        mock_settings.SNOWFLAKE_SERVICE_USER = 'user'
        mock_settings.SNOWFLAKE_SERVICE_USER_PASSWORD = 'pass'
        mock_settings.SNOWFLAKE_ACCOUNT = 'edx.us-east-1'
        SnowflakeCourseProgressSource._get_connection()
        kwargs = mock_connector.connect.call_args[1]
        assert kwargs['user'] == 'user'
        assert kwargs['password'] == 'pass'
        assert kwargs['account'] == 'edx.us-east-1'

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.snowflake.connector')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_connection_includes_optional_role_and_warehouse(self, mock_settings, mock_connector):
        mock_settings.SNOWFLAKE_SERVICE_USER = 'user'
        mock_settings.SNOWFLAKE_SERVICE_USER_PASSWORD = 'pass'
        mock_settings.SNOWFLAKE_ACCOUNT = 'myacct'
        mock_settings.LPR_SNOWFLAKE_WAREHOUSE = 'COMPUTE_WH'
        mock_settings.LPR_SNOWFLAKE_ROLE = 'ANALYST'
        SnowflakeCourseProgressSource._get_connection()
        kwargs = mock_connector.connect.call_args[1]
        assert kwargs['account'] == 'myacct'
        assert kwargs['warehouse'] == 'COMPUTE_WH'
        assert kwargs['role'] == 'ANALYST'


class TestGetCourseProgressMap:
    """Tests for SQL execution, mapping, and cleanup behavior."""

    def test_returns_empty_dict_when_no_pairs(self):
        assert _source().get_course_progress_map(ENTERPRISE_UUID, []) == {}
        assert _source().get_course_progress_map(ENTERPRISE_UUID, [{'user_email': '', 'courserun_key': ''}]) == {}

    @patch.object(SnowflakeCourseProgressSource, '_get_connection')
    @patch.object(SnowflakeCourseProgressSource, '_internal_table', return_value=DEFAULT_TABLE)
    def test_executes_expected_sql_and_params(self, _table, mock_conn_factory):
        ctx, cursor = _mock_ctx_and_cursor(fetchall=[('alice@example.com', 'course-v1:Org+Course+Run', 0.8)])
        mock_conn_factory.return_value = ctx

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'course-v1:Org+Course+Run'},
            {'user_email': 'bob@example.com', 'courserun_key': 'course-v1:Org+Other+Run'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        sql, params = cursor.execute.call_args[0]
        assert DEFAULT_TABLE in sql
        assert 'COURSE_PROGRESS' in sql
        assert 'USER_EMAIL, COURSERUN_KEY' in sql
        assert NORMALIZED_UUID == params[0]
        assert params[1:] == [
            'alice@example.com', 'course-v1:Org+Course+Run',
            'bob@example.com', 'course-v1:Org+Other+Run',
        ]
        assert result == {('alice@example.com', 'course-v1:Org+Course+Run'): 0.8}

    @patch.object(SnowflakeCourseProgressSource, '_get_connection')
    @patch.object(SnowflakeCourseProgressSource, '_internal_table', return_value=DEFAULT_TABLE)
    def test_cursor_and_connection_closed_on_success(self, _table, mock_conn_factory):
        ctx, cursor = _mock_ctx_and_cursor()
        mock_conn_factory.return_value = ctx
        _source().get_course_progress_map(
            ENTERPRISE_UUID,
            [{'user_email': 'alice@example.com', 'courserun_key': 'course-v1:Org+Course+Run'}],
        )
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch.object(SnowflakeCourseProgressSource, '_get_connection')
    @patch.object(SnowflakeCourseProgressSource, '_internal_table', return_value=DEFAULT_TABLE)
    def test_cursor_and_connection_closed_on_execute_error(self, _table, mock_conn_factory):
        ctx, cursor = _mock_ctx_and_cursor()
        cursor.execute.side_effect = RuntimeError('Snowflake error')
        mock_conn_factory.return_value = ctx
        with pytest.raises(RuntimeError, match='Snowflake error'):
            _source().get_course_progress_map(
                ENTERPRISE_UUID,
                [{'user_email': 'alice@example.com', 'courserun_key': 'course-v1:Org+Course+Run'}],
            )
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()
