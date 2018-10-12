"""
Filters for enterprise data views.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import filters

from django.db.models import Q

# Admittedly this is sort of hacky because the use of "|" with 2 Q objects
# forces the ORM to use a LEFT OUTER JOIN, which is needed to return a user
# that has multiple enrollments where at least one has consent_granted=True
CONSENT_TRUE_OR_NOENROLL_Q = Q(enrollments__consent_granted=True) | Q(enrollments__isnull=True)


class ConsentGrantedFilterBackend(filters.BaseFilterBackend):
    """
    Filter backend for any view that needs to filter results where consent has not been granted.

    This requires that `CONSENT_GRANTED_FILTER` be set in the view as a class variable, to identify
    the object's relationship to the consent_granted field.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter a queryset for results where consent has been granted.
        """
        filter_kwargs = {view.CONSENT_GRANTED_FILTER: True}
        return queryset.filter(**filter_kwargs)


class AuditEnrollmentsFilterBackend(filters.BaseFilterBackend):
    """
    Filter backend to exclude enrollments where enrollment mode is `audit`.

    This requires that `ENROLLMENT_MODE_FILTER` be set in the view as a class
    variable, to identify the object's relationship to the
    `user_current_enrollment_mode` field.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter out queryset for results where enrollment mode is `audit`.
        """
        enterprise_id = view.kwargs['enterprise_id']
        enable_audit_enrollment = request.session['enable_audit_enrollment'].get(enterprise_id, False)

        if not enable_audit_enrollment:
            filter_kwargs = {view.ENROLLMENT_MODE_FILTER: 'audit'}
            queryset = queryset.exclude(**filter_kwargs)

        return queryset
