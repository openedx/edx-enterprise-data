"""
Filters for enterprise data views.
"""

from logging import getLogger

from rest_framework import filters

from django.db.models import Q

from enterprise_data.clients import EnterpriseApiClient
from enterprise_data.constants import ANALYTICS_API_VERSION_0, ANALYTICS_API_VERSION_1, ANALYTICS_API_VERSION_ATTR
from enterprise_data.models import EnterpriseLearnerEnrollment

# Admittedly this is sort of hacky because the use of "|" with 2 Q objects
# forces the ORM to use a LEFT OUTER JOIN, which is needed to return a user
# that has multiple enrollments where at least one has consent_granted=True
CONSENT_TRUE_OR_NOENROLL_Q = Q(enrollments__consent_granted=True) | Q(enrollments__isnull=True)
ENROLLMENTS_CONSENT_TRUE_OR_NOENROLL_Q = Q(enrollments__is_consent_granted=True) | Q(enrollments__isnull=True)

LOGGER = getLogger(__name__)


class FiltersMixin:
    """
    Util mixin for enterprise_data filters.
    """

    def update_session_with_enterprise_data(self, request):
        """
        Make cached call to lms to get an enterprise data and update request session.
        """
        enterprise_client = EnterpriseApiClient(request.auth)
        __ = enterprise_client.get_enterprise_and_update_session(request)


class ConsentGrantedFilterBackend(filters.BaseFilterBackend, FiltersMixin):
    """
    Filter backend for any view that needs to filter results where consent has not been granted.

    This requires that `CONSENT_GRANTED_FILTER` be set in the view as a class variable, to identify
    the object's relationship to the consent_granted field.

    If the enterprise is configured for externally managed data sharing consent, all enrollments will be
    returned
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter a queryset for results where consent has been granted.
        """
        current_enterprise = view.kwargs.get('enterprise_id', None)

        self.update_session_with_enterprise_data(request)

        data_sharing_enforce = request.session.get('enforce_data_sharing_consent', {})
        # if the enterprise is configured for "externally managed" data sharing consent,
        # ignore the consent_granted column.
        if data_sharing_enforce.get(current_enterprise, '') != 'externally_managed':
            filter_kwargs = {view.CONSENT_GRANTED_FILTER: True}
            queryset = queryset.filter(**filter_kwargs)
        return queryset


class AuditEnrollmentsFilterBackend(filters.BaseFilterBackend, FiltersMixin):
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

        self.update_session_with_enterprise_data(request)

        enable_audit_data_reporting = request.session['enable_audit_data_reporting'].get(enterprise_id, False)

        if not enable_audit_data_reporting:
            # Filter out enrollments that have audit mode and do not have a coupon code or an offer.
            filter_query = {
                view.ENROLLMENT_MODE_FILTER: 'audit',
                view.COUPON_CODE_FILTER: None,
                view.OFFER_FILTER: None
            }
            queryset = queryset.exclude(**filter_query)

        return queryset


class AuditUsersEnrollmentFilterBackend(filters.BaseFilterBackend, FiltersMixin):
    """
    Filter backend to filter Enterprise Users with 'audit' mode enrollments.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter out queryset on the basis of its enrollment mode.

        If `enable_audit_data_reporting` is not enabled then it will exclude the Users with 'audit' mode enrollment.
        """
        enterprise_id = view.kwargs['enterprise_id']

        self.update_session_with_enterprise_data(request)

        enable_audit_data_reporting = request.session['enable_audit_data_reporting'].get(enterprise_id, False)

        version = getattr(view, ANALYTICS_API_VERSION_ATTR)

        if version == ANALYTICS_API_VERSION_0:
            queryset = queryset if enable_audit_data_reporting else queryset.filter(
                ~Q(enrollments__user_current_enrollment_mode='audit')
            )
        elif version == ANALYTICS_API_VERSION_1:
            if not enable_audit_data_reporting:
                audit_enrollments_enterprise_user_ids = EnterpriseLearnerEnrollment.objects.filter(
                    enterprise_customer_uuid=view.kwargs['enterprise_id'],
                    user_current_enrollment_mode="audit"
                ).values_list(
                    'enterprise_user_id',
                    flat=True
                )
                audit_enrollments_enterprise_user_ids = list(audit_enrollments_enterprise_user_ids)
                LOGGER.info(
                    "[ELV_ANALYTICS_API_V1] Enterprise: [%s], AuditDataReporting: [%s], AuditEnrollments: [%s]",
                    enterprise_id,
                    enable_audit_data_reporting,
                    len(audit_enrollments_enterprise_user_ids)
                )
                queryset = queryset.exclude(enterprise_user_id__in=audit_enrollments_enterprise_user_ids)

        return queryset
