"""
Filters for enterprise data views.
"""

from logging import getLogger

from rest_framework import filters

from django.conf import settings
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

    def get_enterprise_customer(self, enterprise_uuid):
        """
        Return enterprise customer for `enterprise_uuid`.
        """
        enterprise_client = EnterpriseApiClient(
            settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL,
            settings.BACKEND_SERVICE_EDX_OAUTH2_KEY,
            settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )
        return enterprise_client.get_enterprise_customer(enterprise_uuid)


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
        enterprise_uuid = view.kwargs['enterprise_id']
        enterprise_customer = self.get_enterprise_customer(enterprise_uuid)
        # if the enterprise is configured for "externally managed" data sharing consent,
        # ignore the consent_granted column.
        if enterprise_customer.get('enforce_data_sharing_consent') != 'externally_managed':
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

    def exclude_audit_enrollments(self, view):
        """
        Determine if audit enrollments should be excluded.
        """
        # this will be passed from admin-portal to avoid api call to lms
        audit_enrollments = view.request.query_params.get('audit_enrollments')
        if audit_enrollments:
            return audit_enrollments == 'false'

        enterprise_uuid = view.kwargs['enterprise_id']
        enterprise_customer = self.get_enterprise_customer(enterprise_uuid)
        return enterprise_customer.get('enable_audit_data_reporting') is False

    def filter_queryset(self, request, queryset, view):
        """
        Filter out queryset for results where enrollment mode is `audit`.
        """
        if self.exclude_audit_enrollments(view):
            enterprise_uuid = view.kwargs['enterprise_id']
            LOGGER.info(f'[AuditEnrollmentsFilterBackend] excluding audit enrollments for: {enterprise_uuid}')
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
        enterprise_uuid = view.kwargs['enterprise_id']
        enterprise_customer = self.get_enterprise_customer(enterprise_uuid)

        enable_audit_data_reporting = enterprise_customer.get('enable_audit_data_reporting')

        version = getattr(view, ANALYTICS_API_VERSION_ATTR)

        if version == ANALYTICS_API_VERSION_0:
            queryset = queryset if enable_audit_data_reporting else queryset.filter(
                ~Q(enrollments__user_current_enrollment_mode='audit')
            )
        elif version == ANALYTICS_API_VERSION_1:
            if not enable_audit_data_reporting:
                audit_enrollments_enterprise_user_ids = EnterpriseLearnerEnrollment.objects.filter(
                    enterprise_customer_uuid=enterprise_uuid,
                    enterprise_user_id__isnull=False,
                    user_current_enrollment_mode="audit",
                ).values_list(
                    'enterprise_user_id',
                    flat=True
                )
                audit_enrollments_enterprise_user_ids = list(audit_enrollments_enterprise_user_ids)
                LOGGER.info(
                    "[ELV_ANALYTICS_API_V1] Enterprise: [%s], AuditDataReporting: [%s], AuditEnrollments: [%s]",
                    enterprise_uuid,
                    enable_audit_data_reporting,
                    len(audit_enrollments_enterprise_user_ids)
                )
                queryset = queryset.exclude(enterprise_user_id__in=audit_enrollments_enterprise_user_ids)

        return queryset
