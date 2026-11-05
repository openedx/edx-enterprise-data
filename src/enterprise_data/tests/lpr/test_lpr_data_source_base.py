"""
Tests for LPRDataSource base class and LPRSerializerShapeMixin.

Run locally with:
    python -m pytest enterprise_data/tests/lpr/test_lpr_data_source_base.py -v
"""

import uuid

import pytest

from enterprise_data.api.v1.views.lpr_data_source_base import LPRDataSource, LPRSerializerShapeMixin

# ---------------------------------------------------------------------------
# LPRDataSource — abstract interface contracts
# ---------------------------------------------------------------------------


class TestLPRDataSourceInterface:
    """Ensure the base class enforces the interface via NotImplementedError."""

    def test_get_count_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            LPRDataSource().get_count('test-uuid')

    def test_get_count_raises_not_implemented_with_query_params(self):
        with pytest.raises(NotImplementedError):
            LPRDataSource().get_count('test-uuid', query_params={'search': 'alice'})

    def test_get_enrollments_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            LPRDataSource().get_enrollments('test-uuid', limit=10, offset=0)

    def test_get_enrollments_raises_not_implemented_with_query_params(self):
        with pytest.raises(NotImplementedError):
            LPRDataSource().get_enrollments(
                'test-uuid', limit=10, offset=0, query_params={'search': 'alice'}
            )


# ---------------------------------------------------------------------------
# LPRSerializerShapeMixin.normalize_uuid
# ---------------------------------------------------------------------------


class TestNormalizeUuid:
    """normalize_uuid strips hyphens and lowercases."""

    def test_standard_uuid_format(self):
        result = LPRSerializerShapeMixin.normalize_uuid(
            'A1B2C3D4-E5F6-7890-ABCD-EF1234567890'
        )
        assert result == 'a1b2c3d4e5f67890abcdef1234567890'

    def test_already_clean_uuid(self):
        result = LPRSerializerShapeMixin.normalize_uuid('abcdef1234567890abcdef1234567890')
        assert result == 'abcdef1234567890abcdef1234567890'

    def test_uppercase_no_hyphens(self):
        result = LPRSerializerShapeMixin.normalize_uuid('ABCDEF1234567890ABCDEF1234567890')
        assert result == 'abcdef1234567890abcdef1234567890'

    def test_non_string_converts_to_string_first(self):
        u = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
        result = LPRSerializerShapeMixin.normalize_uuid(u)
        assert result == 'a1b2c3d4e5f67890abcdef1234567890'


# ---------------------------------------------------------------------------
# LPRSerializerShapeMixin.enrich
# ---------------------------------------------------------------------------


def _minimal_record(**overrides):
    """Return the smallest valid raw row dict, with optional overrides."""
    base = {
        'enrollment_id': 1,
        'enterprise_enrollment_id': 10,
        'is_consent_granted': True,
        'paid_by': 'Enterprise',
        'user_current_enrollment_mode': 'verified',
        'enrollment_date': '2024-01-01',
        'unenrollment_date': None,
        'unenrollment_end_within_date': None,
        'is_refunded': False,
        'seat_delivery_method': 'Open edX',
        'offer_id': None,
        'offer_name': None,
        'offer_type': None,
        'coupon_code': None,
        'coupon_name': None,
        'contract_id': None,
        'course_list_price': 199.99,
        'amount_learner_paid': 0.0,
        'course_key': 'course-v1:Org+Course+Run',
        'courserun_key': 'course-v1:Org+Course+Run',
        'course_title': 'Test Course',
        'course_pacing_type': 'self_paced',
        'course_start_date': '2024-01-01',
        'course_end_date': '2025-01-01',
        'course_duration_weeks': 8,
        'course_max_effort': 5,
        'course_min_effort': 2,
        'course_primary_program': None,
        'primary_program_type': None,
        'course_primary_subject': 'Computer Science',
        'has_passed': False,
        'last_activity_date': '2024-03-01',
        'progress_status': 'In Progress',
        'passed_date': None,
        'current_grade': 0.72,
        'letter_grade': 'B',
        'enterprise_user_id': 42,
        'user_email': 'alice@example.com',
        'user_account_creation_date': '2020-05-01',
        'user_country_code': 'US',
        'user_username': 'alice',
        'user_first_name': 'Alice',
        'user_last_name': 'Smith',
        'enterprise_name': 'Acme Corp',
        'enterprise_customer_uuid': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'enterprise_sso_uid': '123',
        'created': '2024-01-01T00:00:00Z',
        # Raw fields not in serializer output — must be converted by enrich
        'total_learning_time_seconds': 7200,
        'enterprise_group_name': 'Engineering',
        'enterprise_group_uuid': 'gggg-0000',
        'is_subsidy': True,
        'course_product_line': 'OCM',
        'budget_id': 'bbb-555',
        'course_progress': 0.5,
    }
    base.update(overrides)
    return base


class TestEnrich:
    """LPRSerializerShapeMixin.enrich() correctly shapes and derives fields."""

    def test_only_serializer_fields_are_returned(self):
        record = _minimal_record()
        result = LPRSerializerShapeMixin.enrich(record)
        for key in result:
            assert key in LPRSerializerShapeMixin.SERIALIZER_FIELDS, (
                f'Unexpected field in enrich output: {key}'
            )

    def test_all_serializer_fields_present(self):
        record = _minimal_record()
        result = LPRSerializerShapeMixin.enrich(record)
        for field in LPRSerializerShapeMixin.SERIALIZER_FIELDS:
            assert field in result, f'Missing field in enrich output: {field}'

    def test_total_learning_time_hours_conversion(self):
        record = _minimal_record(total_learning_time_seconds=3600)
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['total_learning_time_hours'] == 1.0

    def test_total_learning_time_hours_rounds_to_2dp(self):
        record = _minimal_record(total_learning_time_seconds=3661)
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['total_learning_time_hours'] == round(3661 / 3600, 2)

    def test_total_learning_time_hours_none_converts_to_zero(self):
        record = _minimal_record(total_learning_time_seconds=None)
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['total_learning_time_hours'] == 0.0

    def test_total_learning_time_hours_zero(self):
        record = _minimal_record(total_learning_time_seconds=0)
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['total_learning_time_hours'] == 0.0

    def test_enterprise_flex_group_name_from_enterprise_group_name(self):
        record = _minimal_record(enterprise_group_name='Engineering')
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['enterprise_flex_group_name'] == 'Engineering'

    def test_enterprise_flex_group_name_none_when_missing(self):
        record = _minimal_record()
        record.pop('enterprise_group_name', None)
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['enterprise_flex_group_name'] is None

    def test_enterprise_flex_group_uuid_from_enterprise_group_uuid(self):
        record = _minimal_record(enterprise_group_uuid='gggg-0000')
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['enterprise_flex_group_uuid'] == 'gggg-0000'

    def test_course_api_url_interpolated_correctly(self):
        record = _minimal_record(
            enterprise_customer_uuid='aaaa-1111',
            courserun_key='course-v1:Org+Test+2024',
        )
        result = LPRSerializerShapeMixin.enrich(record)
        assert result['course_api_url'] == (
            '/enterprise/v1/enterprise-catalogs/aaaa-1111/courses/course-v1:Org+Test+2024'
        )

    def test_raw_fields_not_surfaced(self):
        """Fields used for computation only should not appear in output."""
        record = _minimal_record()
        result = LPRSerializerShapeMixin.enrich(record)
        assert 'total_learning_time_seconds' not in result
        assert 'enterprise_group_name' not in result
        assert 'enterprise_group_uuid' not in result
