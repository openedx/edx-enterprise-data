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
    # TODO: below fields should be removed once admin-portal is switched to V1
    # and code has been updated to handle fields with new names
    consent_granted = serializers.BooleanField(source='is_consent_granted')
    enrollment_created_timestamp = serializers.DateField(source='enrollment_date')
    unenrollment_timestamp = serializers.DateField(source='unenrollment_date')
    offer = serializers.CharField(source='offer_type')
    course_price = serializers.FloatField(source='course_list_price')
    discount_price = serializers.CharField(source='amount_learner_paid')
    course_id = serializers.CharField(source='courserun_key')
    course_start = serializers.DateField(source='course_start_date')
    course_end = serializers.DateField(source='course_end_date')
    passed_timestamp = serializers.DateField(source='passed_date')
    enterprise_id = serializers.UUIDField(source='enterprise_customer_uuid')
    user_account_creation_timestamp = serializers.DateTimeField(source='user_account_creation_date')

    class Meta:
        model = EnterpriseLearnerEnrollment
        exclude = (
            'enterprise_user',
            # TODO: below fields should be removed once admin-portal is switched to V1
            # and code has been updated to handle fields with new names
            'is_consent_granted', 'enrollment_date', 'unenrollment_date', 'offer_type',
            'course_list_price', 'amount_learner_paid', 'courserun_key', 'course_start_date',
            'course_end_date', 'passed_date', 'enterprise_customer_uuid', 'user_account_creation_date',
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
