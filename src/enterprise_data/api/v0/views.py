"""
Views for enterprise api version 0 endpoint.
"""


from datetime import date, timedelta
from logging import getLogger

from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Max, OuterRef, Q, Subquery, Value
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone

from enterprise_data.api.v0 import serializers
from enterprise_data.constants import ANALYTICS_API_VERSION_0
from enterprise_data.filters import (
    CONSENT_TRUE_OR_NOENROLL_Q,
    AuditEnrollmentsFilterBackend,
    AuditUsersEnrollmentFilterBackend,
    ConsentGrantedFilterBackend,
)
from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser
from enterprise_data.paginators import EnterpriseEnrollmentsPagination

LOGGER = getLogger(__name__)


def subtract_one_month(original_date):
    """
    Returns a date exactly one month prior to the passed in date.
    """
    one_day = timedelta(days=1)
    one_month_earlier = original_date - one_day
    while one_month_earlier.month == original_date.month or one_month_earlier.day > original_date.day:
        one_month_earlier -= one_day
    return one_month_earlier


class EnterpriseViewSetMixin(PermissionRequiredMixin):
    """
    Base class for all Enterprise view sets.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = DefaultPagination
    permission_required = 'can_access_enterprise'
    API_VERSION = ANALYTICS_API_VERSION_0

    def paginate_queryset(self, queryset):
        """
        Allows no_page query param to skip pagination
        """
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)


class EnterpriseEnrollmentsViewSet(EnterpriseViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Viewset for routes related to Enterprise course enrollments.
    """
    serializer_class = serializers.EnterpriseEnrollmentSerializer
    pagination_class = EnterpriseEnrollmentsPagination
    filter_backends = (AuditEnrollmentsFilterBackend, ConsentGrantedFilterBackend, filters.OrderingFilter,)
    ordering_fields = '__all__'
    ordering = ('user_email',)
    CONSENT_GRANTED_FILTER = 'consent_granted'
    ENROLLMENT_MODE_FILTER = 'user_current_enrollment_mode'
    COUPON_CODE_FILTER = 'coupon_code'
    OFFER_FILTER = 'offer'

    def get_queryset(self):
        """
        Returns all learner enrollment records for a given enterprise.
        """
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            # See: https://github.com/axnsan12/drf-yasg/issues/333
            return EnterpriseEnrollment.objects.none()

        enterprise_id = self.kwargs['enterprise_id']

        enterprise = EnterpriseUser.objects.filter(enterprise_id=enterprise_id)
        if not enterprise:
            LOGGER.warning(
                "[Data Overview Failure] No enterprise found with id %s from endpoint '%s'. User: %s, Enterprise: %s",
                enterprise_id, self.request.get_full_path(), self.request.user.username, enterprise_id
            )

        enrollments = EnterpriseEnrollment.objects.filter(enterprise_id=enterprise_id)

        enrollments = self.apply_filters(enrollments)
        return enrollments

    def apply_filters(self, queryset):
        """
        Filters enrollments based on query params.
        """
        query_filters = self.request.query_params

        past_week_date = date.today() - timedelta(weeks=1)
        past_month_date = subtract_one_month(date.today())

        passed_date_param = query_filters.get('passed_date')
        if passed_date_param == 'last_week':
            queryset = self.filter_past_week_completions(queryset)

        learner_activity_param = query_filters.get('learner_activity')
        if learner_activity_param:
            queryset = self.filter_active_enrollments(queryset)
        if learner_activity_param == 'active_past_week':
            queryset = self.filter_active_learners(queryset, past_week_date)
        elif learner_activity_param == 'inactive_past_week':
            queryset = self.filter_inactive_learners(queryset, past_week_date)
        elif learner_activity_param == 'inactive_past_month':
            queryset = self.filter_inactive_learners(queryset, past_month_date)

        search_email = query_filters.get('search')
        if search_email:
            queryset = queryset.filter(user_email__icontains=search_email)

        search_course = query_filters.get('search_course')
        if search_course:
            queryset = queryset.filter(course_title__icontains=search_course)
        search_start_date = query_filters.get('search_start_date')
        if search_start_date:
            queryset = queryset.filter(course_start=search_start_date)

        return queryset

    def filter_active_enrollments(self, queryset):
        """
        Filters queryset to include enrollments with course date in future
        and learners have not passed the course yet.
        """
        return queryset.filter(
            has_passed=False,
            course_end__gte=timezone.now(),
        )

    def filter_distinct_learners(self, queryset):
        """
        Filters queryset to include enrollments with a distinct `enterprise_user_id`.
        """
        return queryset.values_list('enterprise_user_id', flat=True).distinct()

    def filter_active_learners(self, queryset, last_activity_date):
        """
        Filters queryset to include enrollments more recent than the specified `last_activity_date`.
        """
        return queryset.filter(last_activity_date__gte=last_activity_date)

    def filter_inactive_learners(self, queryset, last_activity_date):
        """
        Filters queryset to include enrollments more older than the specified `last_activity_date`.
        """
        return queryset.filter(last_activity_date__lte=last_activity_date)

    def filter_distinct_active_learners(self, queryset, last_activity_date):
        """
        Filters queryset to include distinct enrollments more recent than the specified `last_activity_date`.
        """
        return self.filter_distinct_learners(self.filter_active_learners(queryset, last_activity_date))

    def filter_course_completions(self, queryset):
        """
        Filters queryset to include only enrollments that are passing (i.e., completion).
        """
        return queryset.filter(has_passed=1)

    def filter_past_week_completions(self, queryset):
        """
        Filters only those learners who completed a course in last week.
        """
        date_today = timezone.now()
        date_week_before = date_today - timedelta(weeks=1)
        return queryset.filter(
            has_passed=True,
            passed_timestamp__lte=date_today,
            passed_timestamp__gte=date_week_before,
        )

    def filter_number_of_users(self):
        """
        Returns number of enterprise users (enrolled AND not enrolled learners)
        """
        enterprise_id = self.kwargs['enterprise_id']
        return EnterpriseUser.objects.filter(enterprise_id=enterprise_id)

    def get_max_created_date(self, queryset):
        """
        Gets the maximum created timestamp from the queryset.
        """
        created_max = queryset.aggregate(Max('created'))
        return created_max['created__max']

    @action(detail=False)
    def overview(self, request, **kwargs):
        """
        Returns the following data:
            - # of enrolled learners;
            - # of active learners in the past week/month;
            - # of course completions.
            - # of enterprise users (LMS)
        """
        enrollments = self.get_queryset()
        enrollments = self.filter_queryset(enrollments)
        course_completions = self.filter_course_completions(enrollments)
        distinct_learners = self.filter_distinct_learners(enrollments)
        past_week_date = date.today() - timedelta(weeks=1)
        past_month_date = subtract_one_month(date.today())
        active_learners_week = self.filter_distinct_active_learners(enrollments, past_week_date)
        last_updated_date = self.get_max_created_date(enrollments)
        active_learners_month = self.filter_distinct_active_learners(enrollments, past_month_date)
        enterprise_users = self.filter_number_of_users()
        content = {
            'enrolled_learners': distinct_learners.count(),
            'active_learners': {
                'past_week': active_learners_week.count(),
                'past_month': active_learners_month.count(),
            },
            'course_completions': course_completions.count(),
            'last_updated_date': last_updated_date,
            'number_of_users': enterprise_users.count(),
        }
        return Response(content)


class EnterpriseUsersViewSet(EnterpriseViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Viewset for routes related to Enterprise users.
    """
    queryset = EnterpriseUser.objects.all()
    serializer_class = serializers.EnterpriseUserSerializer
    filter_backends = (filters.OrderingFilter, AuditUsersEnrollmentFilterBackend,)
    ordering_fields = '__all__'
    ordering = ('user_email',)

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = queryset.filter(CONSENT_TRUE_OR_NOENROLL_Q).distinct()

        has_enrollments = self.request.query_params.get('has_enrollments')
        if has_enrollments == 'true':
            queryset = queryset.filter(enrollments__isnull=False).distinct()
        elif has_enrollments == 'false':
            queryset = queryset.filter(enrollments__isnull=True)

        active_courses = self.request.query_params.get('active_courses')
        if active_courses == 'true':
            queryset = queryset.filter(
                Q(enrollments__consent_granted=True),
                enrollments__course_end__gte=timezone.now()
            )
        elif active_courses == 'false':
            queryset = queryset.filter(
                Q(enrollments__consent_granted=True),
                enrollments__course_end__lte=timezone.now()
            )

        all_enrollments_passed = self.request.query_params.get('all_enrollments_passed')
        if all_enrollments_passed == 'true':
            queryset = queryset.exclude(enrollments__has_passed=False)
        elif all_enrollments_passed == 'false':
            queryset = queryset.filter(enrollments__has_passed=False)

        extra_fields = self.request.query_params.getlist('extra_fields')
        if 'enrollment_count' in extra_fields:
            enrollment_subquery = (
                EnterpriseEnrollment.objects.filter(
                    enterprise_user=OuterRef("enterprise_user_id"),
                    consent_granted=True,
                )
                .values('enterprise_user')
                .annotate(enrollment_count=Count('pk', distinct=True))
                .values('enrollment_count')
            )
            queryset = queryset.annotate(
                enrollment_count=Coalesce(
                    Subquery(enrollment_subquery, output_field=IntegerField()),
                    Value(0),
                )
            )

        # based on https://stackoverflow.com/questions/43770118/simple-subquery-with-outerref
        if 'course_completion_count' in extra_fields:
            enrollment_subquery = (
                EnterpriseEnrollment.objects.filter(
                    enterprise_user=OuterRef("enterprise_user_id"),
                    has_passed=True,
                    consent_granted=True,
                )
                .values('enterprise_user')
                .annotate(course_completion_count=Count('pk', distinct=True))
                .values('course_completion_count')
            )
            # Coalesce and Value used here so we don't return "null" to the
            # frontend if the count is 0
            queryset = queryset.annotate(
                course_completion_count=Coalesce(
                    Subquery(enrollment_subquery, output_field=IntegerField()),
                    Value(0),
                )
            )
        return queryset

    def list(self, request, **kwargs):  # pylint: disable=arguments-differ
        """
        List view for learner records for a given enterprise.
        """
        enterprise_id = kwargs['enterprise_id']
        users = self.get_queryset().filter(enterprise_id=enterprise_id)

        # do the sorting
        users = self.filter_queryset(users)

        # Bit to account for pagination
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class EnterpriseLearnerCompletedCoursesViewSet(EnterpriseViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    View to manage enterprise learner completed course enrollments.
    """
    serializer_class = serializers.LearnerCompletedCoursesSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = '__all__'
    ordering = ('user_email',)

    def get_queryset(self):
        """
        Returns number of completed courses against each learner.
        """
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            # See: https://github.com/axnsan12/drf-yasg/issues/333
            return EnterpriseEnrollment.objects.none()

        enterprise_id = self.kwargs['enterprise_id']
        # Get the number of completed courses against a learner.
        enrollments = EnterpriseEnrollment.objects.filter(
            enterprise_id=enterprise_id,
            has_passed=True,
            consent_granted=True,
        ).values('user_email').annotate(completed_courses=Count('course_id')).order_by('user_email')
        return enrollments
