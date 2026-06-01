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


def _progress_pair_cache_key(enterprise_customer_uuid, user_email, courserun_key):
    """Build the expected per-pair progress cache key."""
    return get_key(
        'lpr_course_progress',
        SnowflakeCourseProgressSource._internal_table(),
        SnowflakeCourseProgressSource._normalized_enterprise_uuid(enterprise_customer_uuid),
        str(user_email).strip(),
        str(courserun_key).strip(),
    )


def _passing_grade_cache_key(courserun_key):
    """Build the expected passing-grade cache key, including the course overview table name for parity."""
    return get_key('lpr_course_passing_grade', DEFAULT_OVERVIEWS_TABLE, courserun_key)


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

    def test_pair_cache_key_includes_enterprise_table_email_and_courserun(self):
        key = SnowflakeCourseProgressSource._pair_cache_key(
            ENTERPRISE_UUID,
            'alice@example.com',
            'course-v1:org+X+1',
        )
        expected = get_key(
            'lpr_course_progress',
            SnowflakeCourseProgressSource._internal_table(),
            NORMALIZED_UUID,
            'alice@example.com',
            'course-v1:org+X+1',
        )
        assert key == expected

    def test_pair_cache_key_differs_across_enterprises(self):
        first = SnowflakeCourseProgressSource._pair_cache_key(
            ENTERPRISE_UUID,
            'alice@example.com',
            'course-v1:org+X+1',
        )
        second = SnowflakeCourseProgressSource._pair_cache_key(
            '11111111-2222-3333-4444-555555555555',
            'alice@example.com',
            'course-v1:org+X+1',
        )
        assert first != second

# ===========================================================================
# SnowflakeCourseProgressSource — get_course_progress_map
# ===========================================================================


class TestGetCourseProgressMap:
    """Behaviour of the main public method."""

    def test_returns_empty_dict_when_enrollments_empty(self):
        assert not _source().get_course_progress_map(ENTERPRISE_UUID, [])

    def test_returns_empty_dict_when_all_rows_lack_required_fields(self):
        assert not _source().get_course_progress_map(
            ENTERPRISE_UUID,
            [{'user_email': '', 'courserun_key': ''}],
        )

    # Removed duplicate and broken test_cache_stats_are_logged (E0102, E0602)

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_full_cache_hit_skips_snowflake(self, mock_cache):
        """All pairs in cache → Snowflake must not be called."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.side_effect = [
            MagicMock(is_found=True, value=0.8),
            MagicMock(is_found=True, value=0.7),
        ]

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'course1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'course2'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {
            ('alice@example.com', 'course1'): 0.8,
            ('bob@example.com', 'course2'): 0.7,
        }
        mock_cache.set.assert_not_called()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch.object(SnowflakeCourseProgressSource, '_fetch_progress_for_pairs')
    def test_cache_miss_fetches_pairs_from_snowflake(self, mock_fetch, mock_cache):
        """Cache miss fetches and caches only the missing pairs."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)
        mock_fetch.return_value = {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
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
        mock_fetch.assert_called_once_with(
            ENTERPRISE_UUID,
            [('alice@example.com', 'run1'), ('bob@example.com', 'run2')],
        )
        assert mock_cache.set.call_count == 2
        mock_cache.set.assert_any_call(
            _progress_pair_cache_key(ENTERPRISE_UUID, 'alice@example.com', 'run1'),
            0.9,
            timeout=DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
        )
        mock_cache.set.assert_any_call(
            _progress_pair_cache_key(ENTERPRISE_UUID, 'bob@example.com', 'run2'),
            0.7,
            timeout=DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_cache_lookup_uses_enterprise_scoped_keys(self, mock_cache):
        """Cache reads must include the enterprise UUID to avoid cross-enterprise leakage."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=True, value=0.8)

        _source().get_course_progress_map(
            ENTERPRISE_UUID,
            [{'user_email': 'alice@example.com', 'courserun_key': 'course1'}],
        )

        mock_cache.get.assert_called_once_with(
            _progress_pair_cache_key(ENTERPRISE_UUID, 'alice@example.com', 'course1')
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_response_filters_to_requested_pairs_only(self, mock_cache):
        """Only the requested pairs are returned; extra cached pairs are excluded."""
        mock_cache.get_key.side_effect = get_key
        # alice is cached, bob is cached, carol is NOT requested
        mock_cache.get.side_effect = [
            MagicMock(is_found=True, value=0.9),
            MagicMock(is_found=True, value=0.7),
        ]

        enrollments = [
            {'user_email': 'alice@example.com', 'courserun_key': 'run1'},
            {'user_email': 'bob@example.com', 'courserun_key': 'run2'},
        ]
        result = _source().get_course_progress_map(ENTERPRISE_UUID, enrollments)

        assert result == {
            ('alice@example.com', 'run1'): 0.9,
            ('bob@example.com', 'run2'): 0.7,
        }

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    def test_cursor_and_connection_closed_on_success(self, mock_connection_factory):
        """Both cursor and connection must be closed after a successful fetch."""
        ctx, cursor = _mock_ctx_and_cursor()
        mock_connection_factory.return_value = ctx

        _source()._fetch_progress_for_pairs(ENTERPRISE_UUID, [('alice@example.com', 'run1')])
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    def test_cursor_and_connection_closed_on_execute_error(self, mock_connection_factory):
        """Both cursor and connection must be closed even when execute raises."""
        ctx, cursor = _mock_ctx_and_cursor()

        def raise_execute(sql, params=None):
            raise RuntimeError('Snowflake error')
        cursor.execute.side_effect = raise_execute
        mock_connection_factory.return_value = ctx

        with pytest.raises(RuntimeError, match='Snowflake error'):
            _source()._fetch_progress_for_pairs(ENTERPRISE_UUID, [('alice@example.com', 'run1')])
        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.LOGGER')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_cache_stats_are_logged(self, mock_cache, mock_logger):
        """_log_cache_stats must be invoked after every call."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)
        ctx, _ = _mock_ctx_and_cursor(fetchall=[('alice@example.com', 'run1', 0.9)])
        path = 'enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection'
        with patch(path, return_value=ctx):
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
        expected = get_key('lpr_course_passing_grade', DEFAULT_OVERVIEWS_TABLE, 'course-v1:Org+Run')
        assert key == expected


# ===========================================================================
# SnowflakeCoursePassingGradeSource — get_passing_grade_map
# ===========================================================================

class TestGetPassingGradeMap:
    """Behaviour of the main public method."""

    def test_returns_empty_dict_for_empty_input(self):
        assert not _grade_source().get_passing_grade_map([])

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    def test_full_cache_hit_skips_snowflake(self, mock_cache):
        """All courseruns cached → Snowflake must not be called."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=True, value=0.6)

        result = _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        assert result == {'course-v1:Org+Course+Run': 0.6}
        mock_cache.set.assert_not_called()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_absent_keys_stored_as_none_under_negative_ttl(self, _table, mock_connection_factory, mock_cache):
        """Keys not returned by Snowflake are stored as None with the negative TTL."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)

        ctx, _ = _mock_ctx_and_cursor(fetchall=[])
        mock_connection_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        assert result == {'course-v1:Org+Course+Run': None}
        run_key = _passing_grade_cache_key('course-v1:Org+Course+Run')
        mock_cache.set.assert_called_once_with(
            run_key,
            None,
            timeout=DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_mixed_cache_hit_and_miss(self, _table, mock_connection_factory, mock_cache):
        """Cached and fetched values are merged correctly."""
        mock_cache.get_key.side_effect = get_key

        cached_key = 'course-v1:Org+Cached+Run'
        uncached_key = 'course-v1:Org+Uncached+Run'

        def cache_side_effect(cache_key):
            if cache_key == _passing_grade_cache_key(cached_key):
                return MagicMock(is_found=True, value=0.8)
            return MagicMock(is_found=False, value=None)
        mock_cache.get.side_effect = cache_side_effect

        ctx, _ = _mock_ctx_and_cursor(fetchall=[(uncached_key, 0.55)])
        mock_connection_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map([cached_key, uncached_key])

        assert result == {cached_key: 0.8, uncached_key: 0.55}
        mock_cache.set.assert_called_once_with(
            _passing_grade_cache_key(uncached_key),
            0.55,
            timeout=DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT,
        )

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_positive_values_use_24h_timeout(self, _table, mock_connection_factory, mock_cache):
        """Positive cache writes must use the 24-hour TTL."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-v1:Org+Course+Run', 0.7)])
        mock_connection_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        timeout_arg = mock_cache.set.call_args[1].get('timeout')
        assert timeout_arg == DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_single_key_cache_operations_used(self, _table, mock_connection_factory, mock_cache):
        """Each missing key should be cached through the single-key cache API."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-v1:Org+Course+Run', 0.7)])
        mock_connection_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-v1:Org+Course+Run'])

        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_large_key_set_uses_single_query(self, _table, mock_connection_factory, mock_cache):
        """All keys must be fetched in one SQL statement regardless of batch size."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)

        keys = [f'course-{i}' for i in range(1, 6)]
        rows = [(k, round(0.1 * i, 1)) for i, k in enumerate(keys, 1)]
        ctx, cursor = _mock_ctx_and_cursor(fetchall=rows)
        mock_connection_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(keys)

        assert result == {k: round(0.1 * i, 1) for i, k in enumerate(keys, 1)}
        assert cursor.execute.call_count == 1

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_duplicate_keys_deduplicated(self, _table, mock_connection_factory, mock_cache):
        """Duplicate courserun keys must be deduplicated before querying."""
        mock_cache.get_key.side_effect = get_key
        mock_cache.get.return_value = MagicMock(is_found=False, value=None)

        ctx, cursor = _mock_ctx_and_cursor(fetchall=[('course-1', 0.6)])
        mock_connection_factory.return_value = ctx

        result = _grade_source().get_passing_grade_map(['course-1', 'course-1', 'course-1'])

        assert result == {'course-1': 0.6}
        _, params = cursor.execute.call_args[0]
        assert params.count('course-1') == 1

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_cursor_and_connection_closed_on_success(self, _table, mock_connection_factory):
        ctx, cursor = _mock_ctx_and_cursor(fetchall=[])
        mock_connection_factory.return_value = ctx

        _grade_source()._fetch_passing_grades(['course-v1:Org+Course+Run'])

        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_cursor_and_connection_closed_on_execute_error(self, _table, mock_connection_factory):
        ctx, cursor = _mock_ctx_and_cursor()
        cursor.execute.side_effect = RuntimeError('Snowflake error')
        mock_connection_factory.return_value = ctx

        with pytest.raises(RuntimeError, match='Snowflake error'):
            _grade_source()._fetch_passing_grades(['course-v1:Org+Course+Run'])

        cursor.close.assert_called_once()
        ctx.close.assert_called_once()

    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.LOGGER')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake.cache')
    @patch('enterprise_data.api.v1.views.lpr_data_source_snowflake._get_snowflake_connection')
    @patch.object(SnowflakeCoursePassingGradeSource, '_course_overviews_table', return_value=DEFAULT_OVERVIEWS_TABLE)
    def test_logs_cache_and_fetch_observability(self, _table, mock_connection_factory, mock_cache, mock_logger):
        """At least three LOGGER.info calls expected (requested/cached/missing + fetched stats)."""
        mock_cache.get_key.side_effect = get_key

        def cache_side_effect(cache_key):
            if cache_key == _passing_grade_cache_key('course-1'):
                return MagicMock(is_found=True, value=0.5)
            return MagicMock(is_found=False, value=None)
        mock_cache.get.side_effect = cache_side_effect

        ctx, _ = _mock_ctx_and_cursor(fetchall=[('course-2', 0.6)])
        mock_connection_factory.return_value = ctx

        _grade_source().get_passing_grade_map(['course-1', 'course-2'])

        assert mock_logger.info.call_count >= 3
