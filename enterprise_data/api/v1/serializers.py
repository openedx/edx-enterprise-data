"""
Serializers for enterprise api v1.
"""


from datetime import date

from rest_framework import serializers

from enterprise_data.models import EnterpriseLearner, EnterpriseLearnerEnrollment


class EnterpriseLearnerEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseEnrollment model.
    """
    course_api_url = serializers.SerializerMethodField()
    progress_status = serializers.SerializerMethodField()
    has_passed = serializers.BooleanField(default=False, write_only=True)

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_customer_uuid}/courses/{course_run_key}'.format(
            enterprise_customer_uuid=obj.enterprise_customer_uuid, course_run_key=obj.course_run_key
        )

    def get_progress_status(self, obj):
        """
        Return "Passed" if "has_passed" is True.
        Return "In Progress" if "has_passed" is False and course end date has not passed.
        Return "Failed" if "has_passed" is False and course end date has already passed.
        """
        progress_status = "In Progress"
        if obj.has_passed:
            progress_status = "Passed"
        elif obj.course_end_date and obj.course_end_date.date() < date.today():
            progress_status = "Failed"
        return progress_status

    class Meta:
        model = EnterpriseLearnerEnrollment
        exclude = ('created', )


class EnterpriseLearnerSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearner model.
    """

    class Meta:
        model = EnterpriseLearner
        exclude = ('created_at', )

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
