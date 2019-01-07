# -*- coding: utf-8 -*-
"""
Serializers for enterprise api version 0 endpoint.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers

from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser


class EnterpriseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseEnrollment model.
    """
    course_api_url = serializers.SerializerMethodField()
    unenrollment_end_within_date = serializers.SerializerMethodField()

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_id}/courses/{course_id}'.format(
            enterprise_id=obj.enterprise_id, course_id=obj.course_id
        )

    def get_unenrollment_end_within_date(self, obj):
        """
        Return "True" when un-enrolled date is within 14 days of course start or enrollment date
        (whichever is later), else return "False" and return "None" when there is no un-enrollment timestamp.
        """
        unenrollment_within_date = None
        if obj.unenrollment_timestamp:
            unenrollment_within_date = (
                not obj.course_start or
                0 < (obj.unenrollment_timestamp - obj.course_start).days <= 14 or
                0 < (obj.unenrollment_timestamp - obj.enrollment_created_timestamp).days <= 14
            )

        return unenrollment_within_date

    class Meta:
        model = EnterpriseEnrollment
        exclude = ('created', )


class EnterpriseUserSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseUser model.
    """

    class Meta:
        model = EnterpriseUser
        exclude = ('created', )

    def to_representation(self, instance):
        representation = super(EnterpriseUserSerializer, self).to_representation(instance)

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
