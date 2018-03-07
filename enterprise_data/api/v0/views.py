# -*- coding: utf-8 -*-
"""
Views for enterprise api version 0 endpoint.
"""
from __future__ import absolute_import, unicode_literals

from edx_rest_framework_extensions.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import generics

from enterprise_data.api.v0 import serializers
from enterprise_data.filters import ConsentGrantedFilterBackend
from enterprise_data.models import EnterpriseEnrollment
from enterprise_data.permissions import IsStaffOrEnterpriseUser


class EnterpriseEnrollmentsView(generics.ListAPIView):
    """
    The EnterpriseEnrollments view returns all learner enrollment records for a given enterprise
    """
    serializer_class = serializers.EnterpriseEnrollmentSerializer
    pagination_class = DefaultPagination
    authentication_classes = (JwtAuthentication,)
    permission_classes = (IsStaffOrEnterpriseUser,)
    filter_backends = (ConsentGrantedFilterBackend,)
    CONSENT_GRANTED_FILTER = 'consent_granted'

    def get_queryset(self):
        enterprise_id = self.kwargs['enterprise_id']
        return EnterpriseEnrollment.objects.filter(enterprise_id=enterprise_id)
