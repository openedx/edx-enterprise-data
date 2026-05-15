"""
Snowflake helpers for fetching ``course_progress`` and ``course_passing_grade``.

Reads COURSE_PROGRESS from ``PROD.ENTERPRISE.LEARNER_PROGRESS_REPORT_INTERNAL``
and LOWEST_PASSING_GRADE from ``PROD.LMS.COURSE_OVERVIEWS_COURSEOVERVIEW``.
All other LPR data continues to come from the Django ORM.

Required Django settings
------------------------
    SNOWFLAKE_SERVICE_USER
    SNOWFLAKE_SERVICE_USER_PASSWORD

Optional Django settings (with defaults)
-----------------------------------------
    SNOWFLAKE_ACCOUNT                                   = 'edx.us-east-1'
    LPR_SNOWFLAKE_DATABASE                              = 'PROD'
    LPR_SNOWFLAKE_SCHEMA                                = 'ENTERPRISE'
    LPR_SNOWFLAKE_INTERNAL_TABLE                        = 'LEARNER_PROGRESS_REPORT_INTERNAL'
    LPR_COURSE_PROGRESS_CACHE_TIMEOUT                   = 300    (5 minutes)
    LPR_MAX_CACHE_PAYLOAD_BYTES                         = 1048576 (1 MB)
    LPR_SNOWFLAKE_LMS_DATABASE                          = 'PROD'
    LPR_SNOWFLAKE_LMS_SCHEMA                            = 'LMS'
    LPR_SNOWFLAKE_COURSE_OVERVIEWS_TABLE                = 'COURSE_OVERVIEWS_COURSEOVERVIEW'
    LPR_COURSE_PASSING_GRADE_CACHE_TIMEOUT              = 86400  (24 hours)
    LPR_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT     = 3600   (1 hour)
"""

from logging import getLogger
from types import SimpleNamespace

from django.conf import settings

from enterprise_data import cache

LOGGER = getLogger(__name__)

DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT = 60 * 5           # 5 minutes
DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT = 60 * 60  # 1 hour

try:
    import snowflake.connector as snowflake_connector
except ImportError:  # pragma: no cover - depends on runtime extras
    snowflake_connector = None
    LOGGER.warning(
        '[course_progress] snowflake-connector-python is not installed. '
        'course_progress will be null. Add snowflake-connector-python to requirements/base.in.'
    )

snowflake = SimpleNamespace(connector=snowflake_connector)


# ---------------------------------------------------------------------------
# Shared connection factory (module-level to avoid duplication)
# ---------------------------------------------------------------------------

def _get_snowflake_connection():
    """
    Open a Snowflake connection from Django settings.

    Raises:
        ImportError: When snowflake-connector-python is not installed.
        ValueError: When required credentials are absent from settings.
    """
    if snowflake.connector is None:
        raise ImportError(
            'snowflake-connector-python is required for Snowflake LPR access'
        )

    user = getattr(settings, 'SNOWFLAKE_SERVICE_USER', None)
    password = getattr(settings, 'SNOWFLAKE_SERVICE_USER_PASSWORD', None)
    account = getattr(settings, 'SNOWFLAKE_ACCOUNT', 'edx.us-east-1')
    # warehouse and role removed
    if not user or not password:
        LOGGER.error(
            '[snowflake] Credentials missing — '
            'SNOWFLAKE_SERVICE_USER=%s, SNOWFLAKE_SERVICE_USER_PASSWORD=%s.',
            'SET' if user else 'NOT SET',
            'SET' if password else 'NOT SET',
        )
        raise ValueError(
            'SNOWFLAKE_SERVICE_USER and SNOWFLAKE_SERVICE_USER_PASSWORD must both be configured'
        )

    connect_kwargs = {'user': user, 'password': password, 'account': account}
    return snowflake.connector.connect(**connect_kwargs)


# ---------------------------------------------------------------------------
# SnowflakeCourseProgressSource
# ---------------------------------------------------------------------------

class SnowflakeCourseProgressSource:
    """Course progress data source backed by Snowflake.

    Implements chunked, per-courserun caching so that a single large enterprise
    never causes a monolithic cache entry.  Each courserun's data is stored under
    its own cache key; only cache-missing courseruns trigger a Snowflake query.
    """

    # ------------------------------------------------------------------
    # Settings / table helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _internal_table():
        """Return the fully-qualified Snowflake table name for internal LPR data."""
        database = getattr(settings, 'LPR_SNOWFLAKE_DATABASE', 'PROD')
        schema = getattr(settings, 'LPR_SNOWFLAKE_SCHEMA', 'ENTERPRISE')
        table = getattr(settings, 'LPR_SNOWFLAKE_INTERNAL_TABLE', 'LEARNER_PROGRESS_REPORT_INTERNAL')
        return f'{database}.{schema}.{table}'

    @staticmethod
    def _cache_timeout():
        """Return the configurable TTL (seconds) for per-courserun cache entries."""
        return getattr(
            settings,
            'LPR_COURSE_PROGRESS_CACHE_TIMEOUT',
            DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT,
        )

    @staticmethod
    def _max_cache_payload_bytes():
        """Return the maximum allowed serialised payload size in bytes (default 1 MB)."""
        return getattr(settings, 'LPR_MAX_CACHE_PAYLOAD_BYTES', 1024 * 1024)

    # ------------------------------------------------------------------
    # Key normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _normalized_enterprise_uuid(enterprise_customer_uuid):
        """Normalise an enterprise UUID to the Snowflake comparison format (no hyphens, lowercase)."""
        return str(enterprise_customer_uuid).replace('-', '').lower()

    @staticmethod
    def _normalized_row_key(user_email, courserun_key):
        """Return a stable in-memory key for matching ORM rows to Snowflake rows."""
        return (str(user_email).strip().lower(), str(courserun_key).strip())

    # ------------------------------------------------------------------
    # Cache key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_enrollment_cache_key(enterprise_customer_uuid, courserun, user_email):
        """Return the per-enrollment cache key."""
        return cache.get_key(
            'lpr_course_progress',
            SnowflakeCourseProgressSource._internal_table(),
            SnowflakeCourseProgressSource._normalized_enterprise_uuid(enterprise_customer_uuid),
            courserun,
            str(user_email).strip().lower(),
        )

    # ------------------------------------------------------------------
    # Payload size guard
    # ------------------------------------------------------------------

    @staticmethod
    def _should_cache_payload(payload_bytes):
        """Return ``True`` when *payload_bytes* is within the configured size limit."""
        return payload_bytes <= SnowflakeCourseProgressSource._max_cache_payload_bytes()

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    @staticmethod
    def _log_cache_stats(
        requested_courseruns,
        cache_hits,
        cache_misses,
        fetched_rows,
        cache_payloads,
        skipped_caches,
        enterprise_customer_uuid,
    ):
        """Emit structured log lines for cache observability."""
        LOGGER.info(
            '[course_progress] requested_courseruns=%d cache_hits=%d '
            'cache_misses=%d snowflake_rows=%d skipped_cache_writes=%d enterprise=%s',
            len(requested_courseruns),
            len(cache_hits),
            len(cache_misses),
            fetched_rows,
            len(skipped_caches),
            enterprise_customer_uuid,
        )
        for courserun, size in cache_payloads.items():
            LOGGER.info(
                '[course_progress] courserun=%s cache_payload_bytes=%d enterprise=%s',
                courserun,
                size,
                enterprise_customer_uuid,
            )
        for courserun, size in skipped_caches.items():
            LOGGER.warning(
                '[course_progress] skipping cache for courserun=%s enterprise=%s '
                'payload_bytes=%d exceeds limit=%d',
                courserun,
                enterprise_customer_uuid,
                size,
                SnowflakeCourseProgressSource._max_cache_payload_bytes(),
            )

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @staticmethod
    def _get_connection():
        """Delegate to the module-level Snowflake connection factory."""
        return _get_snowflake_connection()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_course_progress_map(self, enterprise_customer_uuid, enrollments):
        """Return a {(user_email, courserun_key): course_progress} mapping, caching per enrollment."""
        # Build (email, courserun) pairs for this page, discarding incomplete rows.
        pairs = [
            self._normalized_row_key(row.get('user_email', ''), row.get('courserun_key', ''))
            for row in enrollments
            if row.get('user_email') and row.get('courserun_key')
        ]
        if not pairs:
            return {}

        # Bulk cache read — one key per (user_email, courserun_key).
        cache_keys = [
            self._get_enrollment_cache_key(enterprise_customer_uuid, courserun, user_email)
            for user_email, courserun in pairs
        ]
        cached = cache.get_many(cache_keys)

        progress_map = {}
        missing_pairs = []
        missing_cache_keys = []
        for pair, cache_key in zip(pairs, cache_keys):
            if cache_key in cached:
                val = cached[cache_key]
                if val is not None:
                    progress_map[pair] = val
            else:
                missing_pairs.append(pair)
                missing_cache_keys.append(cache_key)

        # Fetch missing from Snowflake if needed
        fetched_rows = 0
        cache_payloads = {}
        skipped_caches = {}
        if missing_pairs:
            fetched = self._fetch_progress_for_enrollments(enterprise_customer_uuid, missing_pairs)
            set_entries = {}
            for idx, pair in enumerate(missing_pairs):
                val = fetched.get(pair)
                progress_map[pair] = val if val is not None else None
                set_entries[missing_cache_keys[idx]] = val if val is not None else None
            if set_entries:
                cache.set_many(set_entries, timeout=self._cache_timeout())
            fetched_rows = len(fetched)
        # Log cache stats for observability
        self._log_cache_stats(
            requested_courseruns=pairs,
            cache_hits=[pair for pair in pairs if pair not in missing_pairs],
            cache_misses=missing_pairs,
            fetched_rows=fetched_rows,
            cache_payloads=cache_payloads,
            skipped_caches=skipped_caches,
            enterprise_customer_uuid=enterprise_customer_uuid,
        )
        return {pair: progress_map[pair] for pair in pairs if progress_map.get(pair) is not None}

    # ------------------------------------------------------------------
    # Snowflake queries
    # ------------------------------------------------------------------

    def _fetch_progress_for_enrollments(self, enterprise_customer_uuid, pairs):
        """Fetch progress rows for specific (user_email, courserun_key) pairs from Snowflake."""
        if not pairs:
            return {}

        table = self._internal_table()
        normalized_uuid = self._normalized_enterprise_uuid(enterprise_customer_uuid)
        placeholders = ', '.join(['(%s, %s)'] * len(pairs))
        sql = (
            f"SELECT USER_EMAIL, COURSERUN_KEY, COURSE_PROGRESS "
            f"FROM {table} "
            f"WHERE LOWER(REPLACE(TO_VARCHAR(ENTERPRISE_CUSTOMER_UUID), '-', '')) = %s "
            f"AND (USER_EMAIL, COURSERUN_KEY) IN ({placeholders})"
        )
        # Flatten parameters: [normalized_uuid, email1, course1, email2, course2, ...]
        params = [normalized_uuid] + [item for pair in pairs for item in pair]
        result = {}
        with self._get_connection() as ctx:
            with ctx.cursor() as cs:
                cs.execute(sql, params)
                for row in cs.fetchall():
                    result[self._normalized_row_key(row[0], row[1])] = row[2]
        return result


# ---------------------------------------------------------------------------
# SnowflakeCoursePassingGradeSource
# ---------------------------------------------------------------------------

class SnowflakeCoursePassingGradeSource:
    """Fetches ``lowest_passing_grade`` from Snowflake's LMS course-overviews table.

    Results are cached per courserun key to avoid repeated Snowflake round-trips.
    Absent keys (not present in the table) are stored as ``None`` under a shorter
    negative-cache TTL so that they are re-checked sooner.
    """

    # ------------------------------------------------------------------
    # Settings / table helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _course_overviews_table():
        """Return the fully-qualified Snowflake table name for course overviews."""
        database = getattr(settings, 'LPR_SNOWFLAKE_LMS_DATABASE', 'PROD')
        schema = getattr(settings, 'LPR_SNOWFLAKE_LMS_SCHEMA', 'LMS')
        table = getattr(settings, 'LPR_SNOWFLAKE_COURSE_OVERVIEWS_TABLE', 'COURSE_OVERVIEWS_COURSEOVERVIEW')
        return f'{database}.{schema}.{table}'

    @staticmethod
    def _cache_timeout():
        """Return the configurable TTL (seconds) for positive passing-grade cache entries."""
        return getattr(
            settings,
            'LPR_COURSE_PASSING_GRADE_CACHE_TIMEOUT',
            DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT,
        )

    @staticmethod
    def _negative_cache_timeout():
        """Return the TTL (seconds) for negative (not-found) passing-grade cache entries."""
        return getattr(
            settings,
            'LPR_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT',
            DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT,
        )

    # ------------------------------------------------------------------
    # Cache key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(courserun_key):
        """Return the per-courserun cache key for the passing grade."""
        return cache.get_key('lpr_course_passing_grade', courserun_key)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @staticmethod
    def _get_connection():
        """Delegate to the module-level Snowflake connection factory."""
        return _get_snowflake_connection()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_passing_grade_map(self, courserun_keys):
        """Return a ``{courserun_key: lowest_passing_grade}`` mapping.

        Serves cached values where available and fetches the remainder from
        Snowflake in a single batched query.  Exceptions from cache or
        Snowflake operations propagate; callers are responsible for error
        handling and graceful degradation.

        Args:
            courserun_keys (list[str]): Courserun keys to look up.

        Returns:
            dict: Maps each requested courserun key to its lowest passing
            grade (float) when found, or ``None`` when the key is absent
            from the table.
        """
        if not courserun_keys:
            return {}

        # Deduplicate while preserving order.
        courserun_keys = list(dict.fromkeys(courserun_keys))

        cache_keys_by_courserun = {
            key: self._cache_key(key)
            for key in courserun_keys
        }
        cached_values = cache.get_many(list(cache_keys_by_courserun.values()))

        passing_grade_map = {}
        missing_keys = []

        for courserun_key, cache_key in cache_keys_by_courserun.items():
            if cache_key in cached_values:
                passing_grade_map[courserun_key] = cached_values[cache_key]
            else:
                missing_keys.append(courserun_key)

        LOGGER.info(
            '[course_passing_grade] Requested=%s Cached=%s Missing=%s',
            len(courserun_keys),
            len(passing_grade_map),
            len(missing_keys),
        )

        if missing_keys:
            fetched = self._fetch_passing_grades(missing_keys)
            positive_cache_entries = {}
            negative_cache_entries = {}

            for courserun_key in missing_keys:
                grade = fetched.get(courserun_key)  # None when absent from the table.
                passing_grade_map[courserun_key] = grade
                cache_key = cache_keys_by_courserun[courserun_key]
                if grade is None:
                    negative_cache_entries[cache_key] = None
                else:
                    positive_cache_entries[cache_key] = grade

            if positive_cache_entries:
                cache.set_many(positive_cache_entries, timeout=self._cache_timeout())
            if negative_cache_entries:
                cache.set_many(negative_cache_entries, timeout=self._negative_cache_timeout())

            LOGGER.info(
                '[course_passing_grade] SnowflakeFetched=%s PositiveCached=%s NegativeCached=%s',
                len(fetched),
                len(positive_cache_entries),
                len(negative_cache_entries),
            )

        return passing_grade_map

    # ------------------------------------------------------------------
    # Snowflake queries
    # ------------------------------------------------------------------

    def _fetch_passing_grades(self, courserun_keys):
        """Fetch LOWEST_PASSING_GRADE for *courserun_keys* from Snowflake.

        Args:
            courserun_keys (list[str]): Courserun keys to query.

        Returns:
            dict: ``{courserun_key: lowest_passing_grade}`` for rows found.
        """
        table = self._course_overviews_table()
        placeholders = ', '.join(['%s'] * len(courserun_keys))
        sql = (
            f"SELECT ID, LOWEST_PASSING_GRADE "
            f"FROM {table} "
            f"WHERE ID IN ({placeholders})"
        )

        LOGGER.info(
            '[course_passing_grade] Fetching from Snowflake table=%s requested_keys=%s',
            table,
            len(courserun_keys),
        )

        ctx = self._get_connection()
        cs = ctx.cursor()
        try:
            cs.execute(sql, courserun_keys)
            rows = cs.fetchall()
            LOGGER.info(
                '[course_passing_grade] Snowflake returned rows=%s for requested_keys=%s',
                len(rows),
                len(courserun_keys),
            )
            return {row[0]: row[1] for row in rows}
        finally:
            cs.close()
            ctx.close()
