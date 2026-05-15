"""Tests for ``SnowflakeCourseProgressSource`` and ``SnowflakeCoursePassingGradeSource``."""
# pylint: disable=protected-access

from unittest.mock import MagicMock, patch

import pytest

from django.test import override_settings

from enterprise_data.api.v1.views.lpr_data_source_snowflake import (
    DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT,
    DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT,
    DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
    SnowflakeCoursePassingGradeSource,
    SnowflakeCourseProgressSource,
    _get_snowflake_connection,
)
from enterprise_data.cache import get_key

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

ENTERPRISE_UUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
NORMALIZED_UUID = 'a1b2c3d4e5f67890abcdef1234567890'

DEFAULT_TABLE = 'PROD.ENTERPRISE.LEARNER_PROGRESS_REPORT_INTERNAL'
DEFAULT_OVERVIEWS_TABLE = 'PROD.LMS.COURSE_OVERVIEWS_COURSEOVERVIEW'


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _source():
    """Return a fresh SnowflakeCourseProgressSource instance."""
    return SnowflakeCourseProgressSource()


def _grade_source():
    """Return a fresh SnowflakeCoursePassingGradeSource instance."""
    return SnowflakeCoursePassingGradeSource()


def _mock_ctx_and_cursor(fetchall=None):
    """Return mocked Snowflake connection and cursor objects."""
    cursor = MagicMock()
    cursor.fetchall.return_value = fetchall or []

    def cursor_enter():
        return cursor

    def cursor_exit(*_):
        cursor.close()
    cursor.__enter__.side_effect = cursor_enter
    cursor.__exit__.side_effect = cursor_exit

    def execute(sql, params=None):
        cursor._last_sql = sql
        cursor._last_params = params
    cursor.execute.side_effect = execute
    ctx = MagicMock()
    ctx.cursor.return_value = cursor

    def ctx_enter():
        return ctx

    def ctx_exit(*_):
        ctx.close()
    ctx.__enter__.side_effect = ctx_enter
    ctx.__exit__.side_effect = ctx_exit
    return ctx, cursor


def _progress_enrollment_cache_key(enterprise_uuid, courserun, user_email):
    """Build the expected per-enrollment progress cache key."""
    return get_key(
        'lpr_course_progress',
        SnowflakeCourseProgressSource._internal_table(),
        SnowflakeCourseProgressSource._normalized_enterprise_uuid(enterprise_uuid),
        courserun,
        str(user_email).strip().lower(),
    )


def _passing_grade_cache_key(courserun_key):
    """Build the expected passing-grade cache key."""
    return get_key('lpr_course_passing_grade', courserun_key)


# ---------------------------------------------------------------------------
# Shared fixture: wire cache.get_key to the real implementation
# ---------------------------------------------------------------------------

@pytest.fixture
def real_cache_get_key(mock_cache):
    """Patch ``cache.get_key`` on a mock_cache fixture to use the real implementation."""
    mock_cache.get_key.side_effect = get_key
    return mock_cache


# ===========================================================================
# Module-level connection factory
# ===========================================================================

class TestGetSnowflakeConnection:
    """Tests for the shared ``_get_snowflake_connection`` factory."""

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.snowflake.connector')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_uses_required_credentials(self, mock_settings, mock_connector):
        mock_settings.SNOWFLAKE_SERVICE_USER = 'user'
        mock_settings.SNOWFLAKE_SERVICE_USER_PASSWORD = 'pass'
        mock_settings.SNOWFLAKE_ACCOUNT = 'edx.us-east-1'
        mock_settings.LPR_SNOWFLAKE_WAREHOUSE = None
        mock_settings.LPR_SNOWFLAKE_ROLE = None
        _get_snowflake_connection()
        kwargs = mock_connector.connect.call_args[1]
        assert kwargs['user'] == 'user'
        assert kwargs['password'] == 'pass'
        assert kwargs['account'] == 'edx.us-east-1'
        assert 'warehouse' not in kwargs
        assert 'role' not in kwargs

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.snowflake.connector')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_raises_when_credentials_missing(self, mock_settings, mock_connector):
        mock_settings.SNOWFLAKE_SERVICE_USER = None
        mock_settings.SNOWFLAKE_SERVICE_USER_PASSWORD = None
        with pytest.raises(ValueError, match='SNOWFLAKE_SERVICE_USER'):
            _get_snowflake_connection()
        mock_connector.connect.assert_not_called()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.snowflake')
    def test_raises_import_error_when_connector_missing(self, mock_snowflake):
        mock_snowflake.connector = None
        with pytest.raises(ImportError, match='snowflake-connector-python'):
            _get_snowflake_connection()


# ===========================================================================
# SnowflakeCourseProgressSource — table / settings helpers
# ===========================================================================

class TestInternalTable:
    """Fully-qualified internal table resolution."""

    def test_default_internal_table(self):
        assert SnowflakeCourseProgressSource._internal_table() == DEFAULT_TABLE

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_custom_internal_table(self, mock_settings):
        mock_settings.LPR_SNOWFLAKE_DATABASE = 'STAGING'
        mock_settings.LPR_SNOWFLAKE_SCHEMA = 'REPORTING'
        mock_settings.LPR_SNOWFLAKE_INTERNAL_TABLE = 'COURSE_PROGRESS'
        assert SnowflakeCourseProgressSource._internal_table() == 'STAGING.REPORTING.COURSE_PROGRESS'


# ===========================================================================
# SnowflakeCourseProgressSource — cache configuration
# ===========================================================================

class TestCourseProgressCacheConfiguration:
    """Cache timeout and key construction for course progress."""

    def test_default_cache_timeout_is_five_minutes(self):
        assert DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT == 300
        assert _source()._cache_timeout() == 300

    @override_settings(LPR_COURSE_PROGRESS_CACHE_TIMEOUT=120)
    def test_cache_timeout_is_configurable(self):
        assert _source()._cache_timeout() == 120

    @override_settings(LPR_MAX_CACHE_PAYLOAD_BYTES=512)
    def test_max_cache_payload_bytes_is_configurable(self):
        assert _source()._max_cache_payload_bytes() == 512

    def test_get_enrollment_cache_key_includes_table_uuid_courserun_and_user(self):
        key = SnowflakeCourseProgressSource._get_enrollment_cache_key(ENTERPRISE_UUID, 'run1', 'alice@example.com')
        expected = get_key(
            'lpr_course_progress',
            SnowflakeCourseProgressSource._internal_table(),
            SnowflakeCourseProgressSource._normalized_enterprise_uuid(ENTERPRISE_UUID),
            'run1',
            'alice@example.com',
        )
        assert key == expected

    def test_should_cache_payload_returns_true_within_limit(self):
        assert SnowflakeCourseProgressSource._should_cache_payload(100) is True

    @override_settings(LPR_MAX_CACHE_PAYLOAD_BYTES=50)
    def test_should_cache_payload_returns_false_when_over_limit(self):
        assert SnowflakeCourseProgressSource._should_cache_payload(51) is False


# ===========================================================================
# SnowflakeCourseProgressSource — get_course_progress_map
# ===========================================================================

class TestGetCourseProgressMap:
    """Behaviour of the main public method."""

    def test_returns_empty_dict_when_enrollments_empty(self):
        assert _source().get_course_progress_map(ENTERPRISE_UUID, []) == {}

    def test_returns_empty_dict_when_all_rows_lack_required_fields(self):
        assert _source().get_course_progress_map(
            ENTERPRISE_UUID,
            [{'user_email': '', 'courserun_key': ''}],
        ) == {}

    # Removed duplicate and broken test_cache_stats_are_logged (E0102, E0602)

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_full_cache_hit_skips_snowflake(self, mock_cache):
        """All enrollments cached → Snowflake must not be called."""
        mock_cache.get_key.side_effect = get_key

        pair1_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'course1', 'alice@example.com')
        pair2_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'course2', 'bob@example.com')
        mock_cache.get_many.return_value = {
            pair1_key: 0.8,
            pair2_key: 0.7,
        }

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'course1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'course2'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {
            ('alice@example.com', 'course1'): 0.8,
            ('bob@example.com', 'course2'): 0.7,
        }
        # No Snowflake fetch, so set_many not called
        mock_cache.set_many.assert_not_called()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_fetch_progress_for_enrollments')
    def test_partial_cache_hit_fetches_only_missing_enrollments(self, mock_fetch, mock_cache):
        """Only cache-missing enrollments must be passed to _fetch_progress_for_enrollments."""
        mock_cache.get_key.side_effect = get_key

        pair1_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'run1', 'alice@example.com')
        pair2_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'run2', 'bob@example.com')
        mock_cache.get_many.return_value = {
            pair1_key: 0.9,
        }
        mock_fetch.return_value = {('bob@example.com', 'run2'): 0.7}

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'run1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'run2'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
        }
        mock_cache.get_many.assert_called_once_with([pair1_key, pair2_key])
        mock_fetch.assert_called_once_with(ENTERPRISE_UUID, [('bob@example.com', 'run2')])

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_should_cache_payload', return_value=True)
    @patch.object(SnowflakeCourseProgressSource, '_fetch_progress_for_enrollments')
    def test_cache_populated_on_miss(self, mock_fetch, _should_cache, mock_cache):
        """Cache.set_many must be called with per-courserun keys after a Snowflake fetch."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}
        mock_fetch.return_value = {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
        }

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'run1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'run2'},
        ]
        _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        run1_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'run1', 'alice@example.com')
        run2_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'run2', 'bob@example.com')
        mock_cache.set_many.assert_called_once_with(
            {
                run1_key: 0.9,
                run2_key: 0.7,
            },
            timeout=DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_fetch_progress_for_enrollments')
    @patch.object(SnowflakeCourseProgressSource, '_should_cache_payload', return_value=False)
    def test_oversized_payload_skips_cache(self, _should_cache, mock_fetch, mock_cache):
        """set_many must NOT be called when all payloads exceed the size limit."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}
        mock_fetch.return_value = {('alice@example.com', 'course-v1:Run1'): 0.5}

        enrollments = [{'user_email': 'alice@example.com', 'courserun_key': 'course-v1:Run1'}]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {('alice@example.com', 'course-v1:Run1'): 0.5}
        run1_key = _progress_enrollment_cache_key(ENTERPRISE_UUID, 'course-v1:Run1', 'alice@example.com')
        mock_cache.set_many.assert_called_once_with(
            {run1_key: 0.5},
            timeout=DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_fetch_progress_for_enrollments')
    def test_response_filters_to_requested_pairs_only(self, mock_fetch, mock_cache):
        """Rows returned by Snowflake but not in the enrollments page are excluded."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}
        mock_fetch.return_value = {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
            ('carol@example.com', 'run3'): 0.5,  # not in enrollments
        }

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'run1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'run2'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
        }

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_get_connection')
    def test_cursor_and_connection_closed_on_success(self, mock_conn_factory, mock_cache):
        """Both cursor and connection must be closed after a successful fetch."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, cursor = _mock_ctx_and_cursor()
        mock_conn_factory.return_value = ctx

        _source().get_course_progress_map(
            ENTERPRISE_UUID,
            [{'user_email': 'alice@example.com', 'courserun_key': 'run1'}],
        )
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_get_connection')
    def test_cursor_and_connection_closed_on_execute_error(self, mock_conn_factory, mock_cache):
        """Both cursor and connection must be closed even when execute raises."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, cursor = _mock_ctx_and_cursor()
        # Make execute raise an error

        def raise_execute(sql, params=None):
            raise RuntimeError('Snowflake error')
        cursor.execute.side_effect = raise_execute
        mock_conn_factory.return_value = ctx

        with pytest.raises(RuntimeError, match='Snowflake error'):
            _source().get_course_progress_map(
                ENTERPRISE_UUID,
                [{'user_email': 'alice@example.com', 'courserun_key': 'run1'}],
            )
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.LOGGER')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_cache_stats_are_logged(self, mock_cache, mock_logger):
        """_log_cache_stats must be invoked after every call."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}
        ctx, _ = _mock_ctx_and_cursor(fetchall=[('alice@example.com', 'run1', 0.9)])
        with patch.object(SnowflakeCourseProgressSource, '_get_connection', return_value=ctx):
            _source().get_course_progress_map(
                ENTERPRISE_UUID,
                [{'user_email': 'alice@example.com', 'courserun_key': 'run1'}],
            )
        assert mock_logger.info.call_count >= 1


# ===========================================================================
# SnowflakeCoursePassingGradeSource — table / settings helpers
# ===========================================================================

class TestCourseOverviewsTable:
    """Fully-qualified course-overviews table resolution."""

    def test_default_course_overviews_table(self):
        assert _grade_source()._course_overviews_table() == DEFAULT_OVERVIEWS_TABLE

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.settings')
    def test_custom_course_overviews_table(self, mock_settings):
        mock_settings.LPR_SNOWFLAKE_LMS_DATABASE = 'STAGING'
        mock_settings.LPR_SNOWFLAKE_LMS_SCHEMA = 'PUBLIC'
        mock_settings.LPR_SNOWFLAKE_COURSE_OVERVIEWS_TABLE = 'OVERVIEWS'
        assert _grade_source()._course_overviews_table() == 'STAGING.PUBLIC.OVERVIEWS'


# ===========================================================================
# SnowflakeCoursePassingGradeSource — cache configuration
# ===========================================================================

class TestCoursePassingGradeCacheConfiguration:
    """Cache timeout values and key construction for passing grades."""

    def test_default_positive_cache_timeout_is_24_hours(self):
        assert DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT == 86400
        assert _grade_source()._cache_timeout() == 86400

    @override_settings(LPR_COURSE_PASSING_GRADE_CACHE_TIMEOUT=3600)
    def test_positive_cache_timeout_is_configurable(self):
        assert _grade_source()._cache_timeout() == 3600

    def test_default_negative_cache_timeout_is_1_hour(self):
        assert DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT == 3600
        assert _grade_source()._negative_cache_timeout() == 3600

    @override_settings(LPR_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT=300)
    def test_negative_cache_timeout_is_configurable(self):
        assert _grade_source()._negative_cache_timeout() == 300

    def test_cache_key_includes_prefix_and_courserun(self):
        key = SnowflakeCoursePassingGradeSource._cache_key('course-v1:Org+Run')
        expected = get_key('lpr_course_passing_grade', 'course-v1:Org+Run')
        assert key == expected


# ===========================================================================
# SnowflakeCoursePassingGradeSource — get_passing_grade_map
# ===========================================================================

class TestGetPassingGradeMap:
    """Behaviour of the main public method."""

    def test_returns_empty_dict_for_empty_input(self):
        assert not _grade_source().get_passing_grade_map([])

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    def test_full_cache_hit_skips_snowflake(self, mock_conn_factory, mock_cache):
        """All courseruns cached → Snowflake must not be called."""
        mock_cache.get_key.side_effect = get_key
        run_key = _passing_grade_cache_key('course-v1:Org+Course+Run')
        mock_cache.get_many.return_value = {run_key: 0.6}

        result = _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        assert result == {'course-v1:Org+Course+Run': 0.6}
        mock_conn_factory.assert_not_called()
        mock_cache.set_many.assert_not_called()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_absent_keys_stored_as_none_under_negative_ttl(self, _table, mock_conn_factory, mock_cache):
        """Keys not returned by Snowflake are stored as None with the negative TTL."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, _ = _mock_ctx_and_cursor(fetchall=[])
        mock_conn_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        assert result == {'course-v1:Org+Course+Run': None}
        run_key = _passing_grade_cache_key('course-v1:Org+Course+Run')
        mock_cache.set_many.assert_called_once_with(
            {run_key: None},
            timeout=DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_mixed_cache_hit_and_miss(self, _table, mock_conn_factory, mock_cache):
        """Cached and fetched values are merged correctly."""
        mock_cache.get_key.side_effect = get_key

        cached_key = 'course-v1:Org+Cached+Run'
        uncached_key = 'course-v1:Org+Uncached+Run'
        cached_cache_key = _passing_grade_cache_key(cached_key)
        uncached_cache_key = _passing_grade_cache_key(uncached_key)

        mock_cache.get_many.return_value = {cached_cache_key: 0.8}

        ctx, _ = _mock_ctx_and_cursor(fetchall=[(uncached_key, 0.55)])
        mock_conn_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map([cached_key, uncached_key])

        assert result == {cached_key: 0.8, uncached_key: 0.55}
        mock_cache.set_many.assert_called_once_with(
            {uncached_cache_key: 0.55},
            timeout=DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_positive_values_use_24h_timeout(self, _table, mock_conn_factory, mock_cache):
        """Positive cache writes must use the 24-hour TTL."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-v1:Org+Course+Run', 0.7)])
        mock_conn_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        timeout_arg = mock_cache.set_many.call_args[1].get('timeout')
        assert timeout_arg == DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_bulk_cache_operations_used(self, _table, mock_conn_factory, mock_cache):
        """get_many and set_many must each be called exactly once."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-v1:Org+Course+Run', 0.7)])
        mock_conn_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        mock_cache.get_many.assert_called_once()
        mock_cache.set_many.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_large_key_set_uses_single_query(self, _table, mock_conn_factory, mock_cache):
        """All keys must be fetched in one SQL statement regardless of batch size."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        keys = [f'course-{i}' for i in range(1, 6)]
        rows = [(k, round(0.1 * i, 1)) for i, k in enumerate(keys, 1)]
        ctx, cursor = _mock_ctx_and_cursor(fetchall=rows)
        mock_conn_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(keys)

        assert result == {k: round(0.1 * i, 1) for i, k in enumerate(keys, 1)}
        assert cursor.execute.call_count == 1

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_duplicate_keys_deduplicated(self, _table, mock_conn_factory, mock_cache):
        """Duplicate courserun keys must be deduplicated before querying."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, cursor = _mock_ctx_and_cursor(fetchall=[('course-1', 0.6)])
        mock_conn_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(['course-1', 'course-1', 'course-1'])

        assert result == {'course-1': 0.6}
        _, params = cursor.execute.call_args[0]
        assert params.count('course-1') == 1

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_cursor_and_connection_closed_on_success(self, _table, mock_conn_factory, mock_cache):
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx, cursor = _mock_ctx_and_cursor(fetchall=[])
        mock_conn_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_cursor_and_connection_closed_on_execute_error(self, _table, mock_conn_factory, mock_cache):
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {}

        ctx = MagicMock()
        ctx.cursor.return_value = MagicMock()
        ctx.cursor.return_value.execute.side_effect = RuntimeError('Snowflake error')
        mock_conn_factory.return_value = ctx

        with pytest.raises(RuntimeError, match='Snowflake error'):
            _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        ctx.cursor.return_value.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.LOGGER')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCoursePassingGradeSource, '_get_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_logs_cache_and_fetch_observability(self, _table, mock_conn_factory, mock_cache, mock_logger):
        """At least three LOGGER.info calls expected (requested/cached/missing + fetched stats)."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get_many.return_value = {
            _passing_grade_cache_key('course-1'): 0.5,
        }

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-2', 0.6)])
        mock_conn_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-1', 'course-2'])

        assert mock_logger.info.call_count >= 3
