"""
Snowflake helper for fetching the ``course_progress`` field.

Reads a single column — COURSE_PROGRESS — from
``PROD.ENTERPRISE.LEARNER_PROGRESS_REPORT_INTERNAL`` and merges it into the
existing ORM-backed LPR response.  All other LPR data continues to come from
the Django ORM (EnterpriseLearnerEnrollment) as before.

Required Django settings
------------------------
  SNOWFLAKE_SERVICE_USER
  SNOWFLAKE_SERVICE_USER_PASSWORD

Optional Django settings (with defaults)
-----------------------------------------
  SNOWFLAKE_ACCOUNT                  = 'edx.us-east-1'
  LPR_SNOWFLAKE_DATABASE             = 'PROD'
  LPR_SNOWFLAKE_SCHEMA               = 'ENTERPRISE'
  LPR_SNOWFLAKE_INTERNAL_TABLE       = 'LEARNER_PROGRESS_REPORT_INTERNAL'
  LPR_SNOWFLAKE_WAREHOUSE            = None   (omitted from connection if not set)
  LPR_SNOWFLAKE_ROLE                 = None   (omitted from connection if not set)
"""

from logging import getLogger
from types import SimpleNamespace

from django.conf import settings

LOGGER = getLogger(__name__)

try:
    import snowflake.connector as snowflake_connector
except ImportError:  # pragma: no cover - depends on runtime extras
    snowflake_connector = None
    LOGGER.warning(
        '[course_progress] snowflake-connector-python is not installed. '
        'course_progress will be null. Add snowflake-connector-python to requirements/base.in.'
    )

snowflake = SimpleNamespace(connector=snowflake_connector)


class SnowflakeCourseProgressSource:
    """
    Fetches **only** the ``course_progress`` column from Snowflake's internal
    LPR table (``learner_progress_report_internal``).

    Rows are matched by ``enterprise_customer_uuid`` + ``user_email`` +
    ``courserun_key``, mirroring the composite key used by the ORM queryset.
    """

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_connection():
        """
        Open a Snowflake connection using the same credential settings as
        ``monthly_impact_report.py``.
        """
        if snowflake.connector is None:
            raise ImportError('snowflake-connector-python is required for Snowflake LPR access')

        user = getattr(settings, 'SNOWFLAKE_SERVICE_USER', None)
        password = getattr(settings, 'SNOWFLAKE_SERVICE_USER_PASSWORD', None)
        account = getattr(settings, 'SNOWFLAKE_ACCOUNT', 'edx.us-east-1')
        warehouse = getattr(settings, 'LPR_SNOWFLAKE_WAREHOUSE', None)
        role = getattr(settings, 'LPR_SNOWFLAKE_ROLE', None)

        if not user or not password:
            LOGGER.error(
                '[course_progress] Snowflake credentials missing — '
                'SNOWFLAKE_SERVICE_USER=%s, SNOWFLAKE_SERVICE_USER_PASSWORD=%s.',
                'SET' if user else 'NOT SET',
                'SET' if password else 'NOT SET',
            )
            raise ValueError(
                'SNOWFLAKE_SERVICE_USER and SNOWFLAKE_SERVICE_USER_PASSWORD must both be configured'
            )

        connect_kwargs = {
            'user': user,
            'password': password,
            'account': account,
        }
        if warehouse:
            connect_kwargs['warehouse'] = warehouse
        if role:
            connect_kwargs['role'] = role
        return snowflake.connector.connect(**connect_kwargs)

    @staticmethod
    def _internal_table():
        """Return fully qualified Snowflake table name for internal LPR data."""
        database = getattr(settings, 'LPR_SNOWFLAKE_DATABASE', 'PROD')
        schema = getattr(settings, 'LPR_SNOWFLAKE_SCHEMA', 'ENTERPRISE')
        table = getattr(settings, 'LPR_SNOWFLAKE_INTERNAL_TABLE', 'LEARNER_PROGRESS_REPORT_INTERNAL')
        return f'{database}.{schema}.{table}'

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_course_progress_map(self, enterprise_customer_uuid, enrollments):
        """
        Return a ``{(user_email, courserun_key): course_progress}`` mapping for
        all rows on the current page.

        Args:
            enterprise_customer_uuid (str): The enterprise UUID to scope the query.
            enrollments (list[dict]): Serialized enrollment rows from the ORM page.
                Each dict must contain ``user_email`` and ``courserun_key``.

        Returns:
            dict: Possibly empty mapping; never raises — callers should guard via
            try/except so Snowflake unavailability never breaks the LPR response.
        """
        pairs = [
            (row.get('user_email', ''), row.get('courserun_key', ''))
            for row in enrollments
            if row.get('user_email') and row.get('courserun_key')
        ]
        if not pairs:
            return {}

        table = self._internal_table()
        normalized_uuid = str(enterprise_customer_uuid).replace('-', '').lower()

        # Build parameterised IN list for (user_email, courserun_key) pairs.
        placeholders = ', '.join(['(%s, %s)'] * len(pairs))
        flat_params = [param for pair in pairs for param in pair]

        sql = (
            f"SELECT USER_EMAIL, COURSERUN_KEY, COURSE_PROGRESS "
            f"FROM {table} "
            f"WHERE LOWER(REPLACE(TO_VARCHAR(ENTERPRISE_CUSTOMER_UUID), '-', '')) = %s "
            f"  AND (USER_EMAIL, COURSERUN_KEY) IN ({placeholders})"
        )

        ctx = self._get_connection()
        cs = ctx.cursor()
        try:
            cs.execute(sql, [normalized_uuid] + flat_params)
            rows = cs.fetchall()
            if not rows:
                LOGGER.warning(
                    '[course_progress] Snowflake returned 0 rows for enterprise_uuid=%s. '
                    'Verify LEARNER_PROGRESS_REPORT_INTERNAL contains data for this enterprise.',
                    enterprise_customer_uuid,
                )
            return {
                (row[0], row[1]): row[2]
                for row in rows
            }
        finally:
            cs.close()
            ctx.close()
