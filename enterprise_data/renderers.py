"""
Renderers for enterprise data views.
"""

from rest_framework_csv.renderers import CSVStreamingRenderer


class EnrollmentsCSVRenderer(CSVStreamingRenderer):
    """
    Custom streaming csv renderer for EnterpriseLearnerEnrollment data.
    """

    # This will be used as CSV header for csv generated from `admin-portal`.
    # Do not change the order of fields below. Ordering is important because csv generated
    # on `admin-portal` should match `progress_v3` csv generated in `enterprise_reporting`
    # Order and field names below should match with `EnterpriseLearnerEnrollmentSerializer.fields`
    header = [
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
        'enterprise_customer_uuid', 'enterprise_sso_uid', 'created', 'course_api_url', 'total_learning_time_hours',
        'is_subsidy', 'course_product_line', 'budget_id', 'enterprise_flex_group_name', 'enterprise_flex_group_uuid',
    ]


class IndividualEnrollmentsCSVRenderer(CSVStreamingRenderer):
    """
    Custom streaming csv renderer for advance analytics individual enrollments data.
    """

    header = [
        'email',
        'course_title',
        'course_subject',
        'enroll_type',
        'enterprise_enrollment_date',
    ]


class IndividualCompletionsCSVRenderer(CSVStreamingRenderer):
    """
    Custom streaming csv renderer for advance analytics individual completions data.
    """

    header = [
        'email',
        'course_title',
        'course_subject',
        'enroll_type',
        'passed_date',
    ]


class IndividualEngagementsCSVRenderer(CSVStreamingRenderer):
    """
    Custom streaming csv renderer for advance analytics individual engagements data.
    """

    header = [
        'email',
        'course_title',
        'course_subject',
        'enroll_type',
        'activity_date',
        'learning_time_hours',
    ]


class LeaderboardCSVRenderer(CSVStreamingRenderer):
    """
    Custom streaming csv renderer for advance analytics leaderboard data.
    """

    header = [
        'email',
        'learning_time_hours',
        'session_count',
        'average_session_length',
        'course_completion_count',
    ]
