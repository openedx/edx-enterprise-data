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

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_id}/courses/{course_id}'.format(
            enterprise_id=obj.enterprise_id, course_id=obj.course_id
        )

    class Meta:
        model = EnterpriseEnrollment
        exclude = ('created', )


class EnterpriseUserSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseUser model.
    """

    class Meta:
        model = EnterpriseUser
        fields = '__all__'

    def to_representation(self, obj):
        obj = super(EnterpriseUserSerializer, self).to_representation(obj)
        request = self.context.get('request')
        extra_fields = request.query_params.get('extra_fields')
        if extra_fields is not None:
            if 'enrollment_count' in extra_fields:
                user = EnterpriseUser.objects.get(pk=obj['id'])
                obj['enrollment_count'] = user.enrollments.count()
        return obj
