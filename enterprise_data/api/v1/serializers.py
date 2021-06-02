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
    has_passed = serializers.BooleanField(default=False, write_only=True)
    consent_granted = serializers.BooleanField(source='is_consent_granted')
    enrollment_created_timestamp = serializers.DateField(source='enrollment_date')
    unenrollment_timestamp = serializers.DateField(source='unenrollment_date')
    offer = serializers.CharField(source='offer_type')
    course_price = serializers.DecimalField(source='course_list_price', decimal_places=2, max_digits=12)
    discount_price = serializers.CharField(source='amount_learner_paid')
    course_id = serializers.CharField(source='courserun_key')
    course_start = serializers.DateField(source='course_start_date')
    course_end = serializers.DateField(source='course_end_date')
    passed_timestamp = serializers.DateField(source='passed_date')
    enterprise_id = serializers.UUIDField(source='enterprise_customer_uuid')
    user_account_creation_timestamp = serializers.DateTimeField(source='user_account_creation_date')

    class Meta:
        model = EnterpriseLearnerEnrollment
        fields = (
            'course_api_url', 'has_passed', 'consent_granted', 'enrollment_created_timestamp',
            'unenrollment_timestamp', 'offer', 'course_price', 'discount_price', 'course_id',
            'course_start', 'course_end', 'passed_timestamp', 'enterprise_id', 'user_account_creation_timestamp',
            'user_current_enrollment_mode', 'coupon_code', 'coupon_name', 'course_key', 'course_title',
            'course_pacing_type', 'course_duration_weeks', 'course_max_effort', 'course_min_effort',
            'last_activity_date', 'progress_status', 'current_grade', 'letter_grade', 'user_country_code',
            'user_email', 'user_username', 'enterprise_name', 'enterprise_sso_uid', 'enterprise_user_id',
        )

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_customer_uuid}/courses/{courserun_key}'.format(
            enterprise_customer_uuid=obj.enterprise_customer_uuid, courserun_key=obj.courserun_key
        )


class EnterpriseLearnerSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearner model.
    """
    user_country_code = serializers.CharField(source='lms_user_country')
    enterprise_id = serializers.UUIDField(source='enterprise_customer_uuid')
    user_account_creation_timestamp = serializers.DateTimeField(source='lms_user_created')

    class Meta:
        model = EnterpriseLearner
        fields = (
            'enterprise_id', 'enterprise_user_id', 'user_account_creation_timestamp',
            'lms_user_id', 'user_username', 'user_email', 'enterprise_sso_uid',
            'last_activity_date', 'user_country_code',
        )

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
    user_email = serializers.EmailField()
    completed_courses = serializers.IntegerField()
