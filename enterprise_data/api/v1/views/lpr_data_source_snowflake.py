"""
Snowflake LPR sources for course progress and passing grade.

Classes
-------
SnowflakeCourseProgressSource
    Fetches COURSE_PROGRESS per ``(enterprise_customer_uuid, user_email, courserun_key)``
    from ``LEARNER_PROGRESS_REPORT_INTERNAL``.  Results are cached per (enterprise, pair).

SnowflakeCoursePassingGradeSource
    Fetches LOWEST_PASSING_GRADE per ``courserun_key`` from
    ``COURSE_OVERVIEWS_COURSEOVERVIEW``.  Results are cached per courserun key
    (not enterprise-scoped, since the passing threshold is course-level, not
    enterprise-level).

Required Django settings
------------------------
  SNOWFLAKE_SERVICE_USER
  SNOWFLAKE_SERVICE_USER_PASSWORD

Optional Django settings (with defaults)
-----------------------------------------
  SNOWFLAKE_ACCOUNT                          = 'edx.us-east-1'
  LPR_SNOWFLAKE_WAREHOUSE                    = None
  LPR_SNOWFLAKE_ROLE                         = None
  LPR_SNOWFLAKE_DATABASE                     = 'PROD'
  LPR_SNOWFLAKE_SCHEMA                       = 'ENTERPRISE'
  LPR_SNOWFLAKE_INTERNAL_TABLE               = 'LEARNER_PROGRESS_REPORT_INTERNAL'
  LPR_COURSE_PROGRESS_CACHE_TIMEOUT          = 300    (5 min)
  LPR_SNOWFLAKE_LMS_DATABASE                 = 'PROD'
  LPR_SNOWFLAKE_LMS_SCHEMA                   = 'LMS'
  LPR_SNOWFLAKE_COURSE_OVERVIEWS_TABLE       = 'COURSE_OVERVIEWS_COURSEOVERVIEW'
  LPR_COURSE_PASSING_GRADE_CACHE_TIMEOUT     = 86400  (24 h)
  LPR_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT = 3600  (1 h)
"""

import logging
from contextlib import contextmanager
from types import SimpleNamespace

from django.conf import settings

from enterprise_data import cache

LOGGER = logging.getLogger(__name__)

DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT = 60 * 5           # 5 minutes
DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT = 60 * 60  # 1 hour

# Batch size for Snowflake queries to avoid unbounded SQL and parameter limits.
SNOWFLAKE_QUERY_BATCH_SIZE = 500

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
# Shared connection factory
# ---------------------------------------------------------------------------

def _get_snowflake_connection():
    """
    Open and return a Snowflake connection from Django settings.

    The returned ``SnowflakeConnection`` object supports the context-manager
    protocol (``__enter__`` returns ``self``), so callers should use it inside
    a ``with`` block::

        with _get_snowflake_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)

    Required settings: SNOWFLAKE_SERVICE_USER, SNOWFLAKE_SERVICE_USER_PASSWORD.
    Optional settings: SNOWFLAKE_ACCOUNT (default ``'edx.us-east-1'``),
    LPR_SNOWFLAKE_WAREHOUSE, LPR_SNOWFLAKE_ROLE.

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
    warehouse = getattr(settings, 'LPR_SNOWFLAKE_WAREHOUSE', None)
    role = getattr(settings, 'LPR_SNOWFLAKE_ROLE', None)

    if not user or not password:
        LOGGER.error(
            '[lpr] Snowflake credentials missing — '
            'SNOWFLAKE_SERVICE_USER=%s SNOWFLAKE_SERVICE_USER_PASSWORD=%s.',
            'SET' if user else 'NOT SET',
            'SET' if password else 'NOT SET',
        )
        raise ValueError(
            'SNOWFLAKE_SERVICE_USER and SNOWFLAKE_SERVICE_USER_PASSWORD must both be configured'
        )

    connect_kwargs = {'user': user, 'password': password, 'account': account}
    if warehouse:
        connect_kwargs['warehouse'] = warehouse
    if role:
        connect_kwargs['role'] = role
    return snowflake.connector.connect(**connect_kwargs)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class SnowflakeLPRBaseSource:
    """Shared base for Snowflake LPR data sources.

    Provides a ``_get_setting`` helper and a ``_snowflake_cursor`` context
    manager that wraps the module-level connection factory.  Subclasses only
    need to implement their own SQL and cache-key logic.
    """

    @staticmethod
    def _get_setting(name, default=None):
        """Return the Django setting *name*, or *default* when absent."""
        return getattr(settings, name, default)

    @contextmanager
    def _snowflake_cursor(self):
        """Yield a Snowflake cursor, managing the connection lifecycle.

        Uses ``_get_snowflake_connection()`` (module-level) so that the
        connection factory can be independently mocked in tests.
        """
        with _get_snowflake_connection() as connection:
            with connection.cursor() as cursor:
                yield cursor


# ---------------------------------------------------------------------------
# SnowflakeCourseProgressSource
# ---------------------------------------------------------------------------

class SnowflakeCourseProgressSource(SnowflakeLPRBaseSource):
    """
    Course progress data source backed by Snowflake.

    Fetches COURSE_PROGRESS from ``LEARNER_PROGRESS_REPORT_INTERNAL`` filtered
    by both ``enterprise_customer_uuid`` and the exact ``(user_email,
    courserun_key)`` pairs requested.  Results are cached per pair so that
    repeated page requests never re-query Snowflake for already-seen rows.
    """

    # ------------------------------------------------------------------
    # Settings / table helpers
    # ------------------------------------------------------------------

    @classmethod
    def _internal_table(cls):
        """Return the fully-qualified Snowflake table name for internal LPR data."""
        database = cls._get_setting('LPR_SNOWFLAKE_DATABASE', 'PROD')
        schema = cls._get_setting('LPR_SNOWFLAKE_SCHEMA', 'ENTERPRISE')
        table = cls._get_setting('LPR_SNOWFLAKE_INTERNAL_TABLE', 'LEARNER_PROGRESS_REPORT_INTERNAL')
        return f'{database}.{schema}.{table}'

    @classmethod
    def _cache_timeout(cls):
        """Return the configurable TTL (seconds) for enterprise cache entries."""
        return cls._get_setting('LPR_COURSE_PROGRESS_CACHE_TIMEOUT', DEFAULT_COURSE_PROGRESS_CACHE_TIMEOUT)

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
        return (str(user_email).strip(), str(courserun_key).strip())

    # ------------------------------------------------------------------
    # Cache key helpers
    # ------------------------------------------------------------------

    @classmethod
    def _pair_cache_key(cls, enterprise_customer_uuid, user_email, courserun_key):
        """Return a per-enterprise, per-``(email, courserun_key)`` cache key for course progress."""
        return cache.get_key(
            'lpr_course_progress',
            cls._internal_table(),
            cls._normalized_enterprise_uuid(enterprise_customer_uuid),
            str(user_email).strip(),
            str(courserun_key).strip(),
        )

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    @staticmethod
    def _log_cache_stats(
        requested,
        cache_hits,
        missing,
        snowflake_rows,
        enterprise_customer_uuid,
        negative_cache_hits=0,
    ):
        """
        Emit a structured log line summarising cache efficiency for one request.

        Args:
            requested: Total pairs requested.
            cache_hits: Positive cache hits (pairs with non-None values served from cache).
            missing: Pairs not found in cache, required Snowflake fetch.
            snowflake_rows: Number of rows returned from Snowflake.
            enterprise_customer_uuid: The enterprise UUID being logged.
            negative_cache_hits: Negative cache hits (pairs cached as None, re-verified as absent).
        """
        LOGGER.info(
            (
                '[course_progress] enterprise=%s requested=%d cache_hits=%d '
                'negative_cache_hits=%d missing=%d snowflake_rows=%d'
            ),
            enterprise_customer_uuid,
            requested,
            cache_hits,
            negative_cache_hits,
            missing,
            snowflake_rows,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_course_progress_map(self, enterprise_customer_uuid, enrollments):
        """
        Return a ``{(user_email, courserun_key): course_progress}`` mapping.

        Per-pair cache is checked first; only the cache-missing pairs are sent
        to Snowflake in a single batched query filtered by both enterprise UUID
        and the exact ``(USER_EMAIL, COURSERUN_KEY)`` pairs.

        Return-value contract: only pairs that have a non-``None`` progress
        value are included in the returned mapping.  Pairs absent from
        Snowflake (cached as ``None`` to prevent repeated round-trips) are
        **not** present as keys in the result.  This differs from
        ``SnowflakeCoursePassingGradeSource.get_passing_grade_map``, which
        **does** include absent keys mapped to ``None``.

        Error contract: exceptions from Snowflake or cache operations propagate
        to the caller.  The viewset wraps this method in ``try/except Exception``
        and gracefully degrades (returns ``None`` for the field) on failure.
        This contract is intentionally the same as
        ``SnowflakeCoursePassingGradeSource.get_passing_grade_map`` — both
        sources raise on error rather than silently swallowing exceptions.
        """
        # Deduplicate while preserving order.
        requested_pairs = list(dict.fromkeys(
            self._normalized_row_key(row.get('user_email', ''), row.get('courserun_key', ''))
            for row in enrollments
            if row.get('user_email') and row.get('courserun_key')
        ))
        if not requested_pairs:
            return {}

        progress_map = {}
        missing_pairs = []
        positive_cache_hits = 0
        negative_cache_hits = 0

        # Batch cache lookup: one round-trip for all pairs instead of N.
        pair_to_cache_key = {
            pair: self._pair_cache_key(enterprise_customer_uuid, *pair)
            for pair in requested_pairs
        }
        cached_values = cache.get_many(list(pair_to_cache_key.values()))
        for pair, ck in pair_to_cache_key.items():
            if ck in cached_values:
                if cached_values[ck] is not None:
                    progress_map[pair] = cached_values[ck]
                    positive_cache_hits += 1
                else:
                    # Negative cache hit: pair was queried before, not in Snowflake.
                    negative_cache_hits += 1
            else:
                missing_pairs.append(pair)

        snowflake_rows = {}
        if missing_pairs:
            snowflake_rows = self._fetch_progress_for_pairs(enterprise_customer_uuid, missing_pairs)
            writes = {}
            for pair in missing_pairs:
                grade = snowflake_rows.get(pair)
                if grade is not None:
                    progress_map[pair] = grade
                # Cache positive hits and misses (None) alike to prevent
                # repeated Snowflake round-trips for pairs not in the table.
                writes[pair_to_cache_key[pair]] = grade
            # Batch cache write: one round-trip for all missing pairs.
            cache.set_many(writes, timeout=self._cache_timeout())

        self._log_cache_stats(
            requested=len(requested_pairs),
            cache_hits=positive_cache_hits,
            negative_cache_hits=negative_cache_hits,
            missing=len(missing_pairs),
            snowflake_rows=len(snowflake_rows),
            enterprise_customer_uuid=enterprise_customer_uuid,
        )
        return progress_map

    # ------------------------------------------------------------------
    # Snowflake queries
    # ------------------------------------------------------------------

    def _fetch_progress_for_pairs(self, enterprise_customer_uuid, pairs):
        """
        Fetch COURSE_PROGRESS from Snowflake for specific ``(user_email, courserun_key)`` pairs.

        Filters by both enterprise UUID and the exact set of pairs so only the
        rows needed are transferred from Snowflake — never the full enterprise
        table.

        Args:
            enterprise_customer_uuid: The enterprise UUID.
            pairs (list[tuple[str, str]]): Deduplicated (user_email, courserun_key) tuples.

        Returns:
            dict: ``{(user_email, courserun_key): course_progress}`` for found rows.
        """
        if not pairs:
            return {}

        table = self._internal_table()
        normalized_uuid = self._normalized_enterprise_uuid(enterprise_customer_uuid)

        # Chunk the pairs into fixed-size batches so that large pages do not
        # produce unbounded SQL statements or hit Snowflake's parameter limits.
        result = {}
        for batch_start in range(0, len(pairs), SNOWFLAKE_QUERY_BATCH_SIZE):
            batch = pairs[batch_start: batch_start + SNOWFLAKE_QUERY_BATCH_SIZE]

            # Row-value constructor: ``(USER_EMAIL, COURSERUN_KEY) IN ((%s,%s), ...)``
            # Requires snowflake-connector-python >= 2.7.0.
            placeholders = ', '.join(['(%s, %s)'] * len(batch))
            flat_params = [val for pair in batch for val in pair]

            # Table name from Django settings — safe to interpolate.
            sql = (
                f"SELECT USER_EMAIL, COURSERUN_KEY, COURSE_PROGRESS "
                f"FROM {table} "
                f"WHERE LOWER(REPLACE(TO_VARCHAR(ENTERPRISE_CUSTOMER_UUID), '-', '')) = %s "
                f"  AND (USER_EMAIL, COURSERUN_KEY) IN ({placeholders})"
            )

            LOGGER.info(
                '[course_progress] querying Snowflake table=%s enterprise=%s pairs=%d (batch %d-%d)',
                table, enterprise_customer_uuid, len(pairs), batch_start, batch_start + len(batch) - 1,
            )

            with self._snowflake_cursor() as cursor:
                cursor.execute(sql, [normalized_uuid] + flat_params)
                rows = cursor.fetchall()

            if not rows:
                LOGGER.warning(
                    '[course_progress] Snowflake returned 0 rows for enterprise=%s pairs=%d (batch %d). '
                    'Verify LEARNER_PROGRESS_REPORT_INTERNAL contains data for this enterprise.',
                    enterprise_customer_uuid, len(batch), batch_start,
                )
            else:
                LOGGER.info(
                    '[course_progress] Snowflake returned rows=%d for pairs=%d (batch %d)',
                    len(rows), len(batch), batch_start,
                )

            for row in rows:
                result[self._normalized_row_key(row[0], row[1])] = row[2]

        return result


# ---------------------------------------------------------------------------
# SnowflakeCoursePassingGradeSource
# ---------------------------------------------------------------------------


class SnowflakeCoursePassingGradeSource(SnowflakeLPRBaseSource):
    """
    Fetches ``lowest_passing_grade`` from Snowflake's LMS course-overviews table.

    Results are cached per courserun key to avoid repeated Snowflake round-trips.
    Absent keys (not present in the table) are stored as ``None`` under a shorter
    negative-cache TTL so that they are re-checked sooner.
    """

    # ------------------------------------------------------------------
    # Settings / table helpers
    # ------------------------------------------------------------------

    @classmethod
    def _course_overviews_table(cls):
        """Return the fully-qualified Snowflake table name for course overviews."""
        database = cls._get_setting('LPR_SNOWFLAKE_LMS_DATABASE', 'PROD')
        schema = cls._get_setting('LPR_SNOWFLAKE_LMS_SCHEMA', 'LMS')
        table = cls._get_setting('LPR_SNOWFLAKE_COURSE_OVERVIEWS_TABLE', 'COURSE_OVERVIEWS_COURSEOVERVIEW')
        return f'{database}.{schema}.{table}'

    @classmethod
    def _cache_timeout(cls):
        """Return the configurable TTL (seconds) for positive passing-grade cache entries."""
        return cls._get_setting(
            'LPR_COURSE_PASSING_GRADE_CACHE_TIMEOUT',
            DEFAULT_COURSE_PASSING_GRADE_CACHE_TIMEOUT,
        )

    @classmethod
    def _negative_cache_timeout(cls):
        """Return the TTL (seconds) for negative (not-found) passing-grade cache entries."""
        return cls._get_setting(
            'LPR_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT',
            DEFAULT_COURSE_PASSING_GRADE_NEGATIVE_CACHE_TIMEOUT,
        )

    # ------------------------------------------------------------------
    # Cache key helpers
    # ------------------------------------------------------------------

    @classmethod
    def _cache_key(cls, courserun_key):
        """
        Return the per-courserun-key cache key for the lowest passing grade.

        The key is intentionally **not** enterprise-scoped: ``LOWEST_PASSING_GRADE``
        is a course-level attribute stored in the LMS course-overviews table and
        is the same threshold for all enterprises enrolling in that course.
        """
        return cache.get_key(
            'lpr_course_passing_grade',
            cls._course_overviews_table(),
            courserun_key,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_passing_grade_map(self, courserun_keys):
        """Return a ``{courserun_key: lowest_passing_grade}`` mapping.

        Serves cached values where available and fetches the remainder from
        Snowflake in a single batched query.  Exceptions from cache or Snowflake
        operations propagate; callers are responsible for error handling and
        graceful degradation (same contract as
        ``SnowflakeCourseProgressSource.get_course_progress_map``).

        Return-value contract: every requested key is present in the returned
        mapping.  Keys absent from Snowflake are mapped to ``None`` (and cached
        under a shorter negative TTL to prevent repeated round-trips).  This
        differs from ``SnowflakeCourseProgressSource.get_course_progress_map``,
        which **omits** absent keys from the result entirely.

        Security note: the cache key for passing grades is **not** enterprise-
        scoped because ``LOWEST_PASSING_GRADE`` is a course-level attribute
        identical across all enterprises.  Callers **must** only supply
        courserun keys that were obtained from the requesting enterprise's
        filtered enrollment queryset; passing attacker-influenced keys that
        do not belong to the enterprise is not supported and would return
        that course's threshold from cache or Snowflake.

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

        cache_key_map = {key: self._cache_key(key) for key in courserun_keys}

        passing_grade_map = {}
        missing_keys = []

        # Batch cache lookup: one round-trip for all keys instead of N.
        cached_values = cache.get_many(list(cache_key_map.values()))
        for courserun_key, ck in cache_key_map.items():
            if ck in cached_values:
                passing_grade_map[courserun_key] = cached_values[ck]
            else:
                missing_keys.append(courserun_key)

        LOGGER.info(
            '[course_passing_grade] requested=%d cache_hits=%d missing=%d',
            len(courserun_keys), len(passing_grade_map), len(missing_keys),
        )

        if missing_keys:
            fetched = self._fetch_passing_grades(missing_keys)
            positive_count = 0
            negative_count = 0
            positive_writes = {}
            negative_writes = {}

            for courserun_key in missing_keys:
                grade = fetched.get(courserun_key)  # None when absent from the table
                passing_grade_map[courserun_key] = grade
                ck = cache_key_map[courserun_key]
                if grade is None:
                    negative_writes[ck] = None
                    negative_count += 1
                else:
                    positive_writes[ck] = grade
                    positive_count += 1

            # Batch cache writes: one round-trip each for positive and negative sets.
            if positive_writes:
                cache.set_many(positive_writes, timeout=self._cache_timeout())
            if negative_writes:
                cache.set_many(negative_writes, timeout=self._negative_cache_timeout())

            LOGGER.info(
                '[course_passing_grade] snowflake_rows=%d positive_cached=%d negative_cached=%d',
                len(fetched), positive_count, negative_count,
            )

        return passing_grade_map

    # ------------------------------------------------------------------
    # Snowflake queries
    # ------------------------------------------------------------------

    def _fetch_passing_grades(self, courserun_keys):
        """Fetch LOWEST_PASSING_GRADE for *courserun_keys* from Snowflake.

        Args:
            courserun_keys (list[str]): Courserun keys to query.  Must be
                non-empty (the caller ``get_passing_grade_map`` guarantees
                this, and the method also guards itself).

        Returns:
            dict: ``{courserun_key: lowest_passing_grade}`` for rows found.
        """
        if not courserun_keys:
            return {}

        table = self._course_overviews_table()

        # Chunk the keys into fixed-size batches so that large pages do not
        # produce unbounded SQL statements or hit Snowflake's parameter limits.
        result = {}
        for batch_start in range(0, len(courserun_keys), SNOWFLAKE_QUERY_BATCH_SIZE):
            batch = courserun_keys[batch_start: batch_start + SNOWFLAKE_QUERY_BATCH_SIZE]
            placeholders = ', '.join(['%s'] * len(batch))

            # Table name from Django settings — safe to interpolate.
            # ID is the courserun key string (e.g. ``course-v1:org+X+1``).
            sql = (
                f"SELECT ID AS COURSERUN_KEY, LOWEST_PASSING_GRADE "
                f"FROM {table} "
                f"WHERE ID IN ({placeholders})"
            )

            LOGGER.info(
                '[course_passing_grade] querying Snowflake table=%s keys=%d (batch %d-%d)',
                table, len(courserun_keys), batch_start, batch_start + len(batch) - 1,
            )

            with self._snowflake_cursor() as cursor:
                cursor.execute(sql, batch)
                rows = cursor.fetchall()

            LOGGER.info(
                '[course_passing_grade] Snowflake returned %d row(s) for %d requested key(s) (batch %d).',
                len(rows), len(batch), batch_start,
            )
            result.update({row[0]: row[1] for row in rows})

        return result
