"""
Filters for enterprise data views.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import filters


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
