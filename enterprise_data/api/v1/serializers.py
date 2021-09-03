"""
Serializers for enterprise api v1.
"""


from rest_framework import serializers

from enterprise_data.models import EnterpriseLearner, EnterpriseLearnerEnrollment


class EnterpriseLearnerEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearnerEnrollment model.
    """
    course_api_url = serializers.SerializerMethodField()
    enterprise_user_id = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseLearnerEnrollment
        # Do not change the order of fields below. Ordering is important becuase `progress_v3`
        # csv generated in `enterprise_reporting` should be same as csv generated on `admin-portal`
        # Order and field names below should match with `EnterpriseLearnerEnrollmentViewSet.header`
        fields = (
            'enrollment_id', 'enterprise_enrollment_id', 'is_consent_granted', 'paid_by',
            'user_current_enrollment_mode', 'enrollment_date', 'unenrollment_date',
            'unenrollment_end_within_date', 'is_refunded', 'seat_delivery_method',
            'offer_name', 'offer_type', 'coupon_code', 'coupon_name', 'contract_id',
            'course_list_price', 'amount_learner_paid', 'course_key', 'courserun_key',
            'course_title', 'course_pacing_type', 'course_start_date', 'course_end_date',
            'course_duration_weeks', 'course_max_effort', 'course_min_effort',
            'course_primary_program', 'course_primary_subject', 'has_passed',
            'last_activity_date', 'progress_status', 'passed_date', 'current_grade',
            'letter_grade', 'enterprise_user_id', 'user_email', 'user_account_creation_date',
            'user_country_code', 'user_username', 'enterprise_name', 'enterprise_customer_uuid',
            'enterprise_sso_uid', 'created', 'course_api_url',
        )

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_customer_uuid}/courses/{courserun_key}'.format(
            enterprise_customer_uuid=obj.enterprise_customer_uuid, courserun_key=obj.courserun_key
        )

    def get_enterprise_user_id(self, obj):
        """Returns enterprise user id of a learner's enrollment"""
        return obj.enterprise_user_id


class EnterpriseLearnerSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearner model.
    """

    class Meta:
        model = EnterpriseLearner
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if hasattr(instance, 'enrollment_count'):
            representation['enrollment_count'] = instance.enrollment_count
        if hasattr(instance, 'course_completion_count'):
            representation['course_completion_count'] = instance.course_completion_count

        return representation


class LearnerCompletedCoursesSerializer(serializers.Serializer):    # pylint: disable=abstract-method
    """
    Serializer for learner's completed courses.
    """
    class Meta:
        ref_name = 'v1.LearnerCompletedCoursesSerializer'

    user_email = serializers.EmailField()
    completed_courses = serializers.IntegerField()
