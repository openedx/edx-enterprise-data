"""Shared contracts and helpers for LPR data sources."""


class LPRDataSource:
    """Abstract base class for Learner Progress Report data sources."""

    def get_count(self, enterprise_customer_uuid, query_params=None):
        """Return total number of enrollment rows for the given enterprise."""
        raise NotImplementedError

    def get_enrollments(self, enterprise_customer_uuid, limit, offset, query_params=None):
        """Return one page of enrollment rows as serializer-shaped dictionaries."""
        raise NotImplementedError


class LPRSerializerShapeMixin:
    """Shared serializer output shaping for different LPR backends."""

    SERIALIZER_FIELDS = (
        'enrollment_id', 'enterprise_enrollment_id', 'is_consent_granted', 'paid_by',
        'user_current_enrollment_mode', 'enrollment_date', 'unenrollment_date',
        'unenrollment_end_within_date', 'is_refunded', 'seat_delivery_method',
        'offer_id', 'offer_name', 'offer_type', 'coupon_code', 'coupon_name', 'contract_id',
        'course_list_price', 'amount_learner_paid', 'course_key', 'courserun_key',
        'course_title', 'course_pacing_type', 'course_start_date', 'course_end_date',
        'course_duration_weeks', 'course_max_effort', 'course_min_effort',
        'course_primary_program', 'primary_program_type', 'course_primary_subject', 'has_passed',
        'last_activity_date', 'progress_status', 'passed_date', 'current_grade',
        'letter_grade', 'enterprise_user_id', 'user_email', 'user_account_creation_date',
        'user_country_code', 'user_username', 'user_first_name', 'user_last_name', 'enterprise_name',
        'enterprise_customer_uuid', 'enterprise_sso_uid', 'created', 'course_api_url',
        'total_learning_time_hours', 'is_subsidy', 'course_product_line', 'budget_id',
        'enterprise_flex_group_name', 'enterprise_flex_group_uuid',
        'course_progress',
    )

    @staticmethod
    def normalize_uuid(uuid_value):
        """Strip hyphens and lowercase for backend-agnostic UUID matching."""
        return str(uuid_value).replace('-', '').lower()

    @classmethod
    def enrich(cls, record):
        """Compute derived serializer fields and filter to API contract fields."""
        enterprise_uuid = record.get('enterprise_customer_uuid', '')
        courserun_key = record.get('courserun_key', '')
        record['course_api_url'] = (
            f'/enterprise/v1/enterprise-catalogs/{enterprise_uuid}/courses/{courserun_key}'
        )

        try:
            seconds = float(record.get('total_learning_time_seconds') or 0)
        except (TypeError, ValueError):
            seconds = 0.0
        record['total_learning_time_hours'] = round(seconds / 3600, 2)

        record['enterprise_flex_group_name'] = record.get('enterprise_group_name') or None
        record['enterprise_flex_group_uuid'] = record.get('enterprise_group_uuid') or None

        return {field: record.get(field) for field in cls.SERIALIZER_FIELDS}
