"""
Views for enterprise api v1.
"""


from datetime import date, timedelta
from logging import getLogger

from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Max, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone

from enterprise_data.api.v1 import serializers
from enterprise_data.constants import ANALYTICS_API_VERSION_1
from enterprise_data.filters import AuditEnrollmentsFilterBackend, AuditUsersEnrollmentFilterBackend
from enterprise_data.models import EnterpriseLearner, EnterpriseLearnerEnrollment
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


class EnterpriseViewSet(PermissionRequiredMixin, viewsets.ViewSet):
    """
    Base class for all Enterprise view sets.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = DefaultPagination
    permission_required = 'can_access_enterprise'
    API_VERSION = ANALYTICS_API_VERSION_1

    def paginate_queryset(self, queryset):
        """
        Allows no_page query param to skip pagination
        """
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)  # pylint: disable=no-member


class EnterpriseLearnerEnrollmentViewSet(EnterpriseViewSet, viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise course enrollments.
    """
    serializer_class = serializers.EnterpriseLearnerEnrollmentSerializer
    pagination_class = EnterpriseEnrollmentsPagination
    filter_backends = (AuditEnrollmentsFilterBackend, filters.OrderingFilter,)
    ordering_fields = '__all__'
    ordering = ('user_email',)
    ENROLLMENT_MODE_FILTER = 'user_current_enrollment_mode'
    COUPON_CODE_FILTER = 'coupon_code'
    OFFER_FILTER = 'offer_type'
    # This will be used as CSV header for csv generated from `admin-portal`.
    # Do not change the order of fields below. Ordering is important because csv generated
    # on `admin-portal` should match `progress_v3` csv generated in `enterprise_reporting`
    # Order and field names below should match with `EnterpriseLearnerEnrollmentSerializer.fields`
    header = [
        'enrollment_id', 'enterprise_enrollment_id', 'is_consent_granted', 'paid_by',
        'user_current_enrollment_mode', 'enrollment_date', 'unenrollment_date',
        'unenrollment_end_within_date', 'is_refunded', 'seat_delivery_method',
        'offer_name', 'offer_type', 'coupon_code', 'coupon_name', 'contract_id',
        'course_list_price', 'amount_learner_paid', 'course_key', 'courserun_key',
        'course_title', 'course_pacing_type', 'course_start_date', 'course_end_date',
        'course_duration_weeks', 'course_max_effort', 'course_min_effort',
        'course_primary_program', 'course_primary_subject', 'has_passed',
        'last_activity_date', 'progress_status', 'passed_date', 'current_grade',
        'letter_grade', 'enterprise_user_id', 'user_email', 'user_account_creation_date',
        'user_country_code', 'user_username', 'enterprise_name', 'enterprise_customer_uuid',
        'enterprise_sso_uid', 'created', 'course_api_url',
    ]

    def get_renderer_context(self):
        renderer_context = super().get_renderer_context()
        renderer_context['header'] = self.header
        return renderer_context

    def get_queryset(self):
        """
        Returns all learner enrollment records for a given enterprise.
        """
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            # See: https://github.com/axnsan12/drf-yasg/issues/333
            return EnterpriseLearnerEnrollment.objects.none()

        enterprise_customer_uuid = self.kwargs['enterprise_id']

        enterprise = EnterpriseLearner.objects.filter(enterprise_customer_uuid=enterprise_customer_uuid)
        if not enterprise:
            LOGGER.warning(
                "[Data Overview Failure] Wrong Enterprise UUID. UUID [%s], Endpoint ['%s'], User: [%s]",
                enterprise_customer_uuid,
                self.request.get_full_path(),
                self.request.user.username,
            )

        enrollments = EnterpriseLearnerEnrollment.objects.filter(enterprise_customer_uuid=enterprise_customer_uuid)

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
            queryset = queryset.filter(course_start_date=search_start_date)

        return queryset

    def filter_active_enrollments(self, queryset):
        """
        Filters queryset to include enrollments with course date in future
        and learners have not passed the course yet.
        """
        return queryset.filter(
            has_passed=False,
            course_end_date__gte=timezone.now(),
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
            passed_date__lte=date_today,
            passed_date__gte=date_week_before,
        )

    def filter_number_of_users(self):
        """
        Returns number of enterprise users (enrolled AND not enrolled learners)
        """
        return EnterpriseLearner.objects.filter(enterprise_customer_uuid=self.kwargs['enterprise_id'])

    def get_max_created_date(self, queryset):
        """
        Gets the maximum created timestamp from the queryset.
        """
        created_max = queryset.aggregate(Max('created'))
        return created_max['created__max']

    @action(detail=False)
    def overview(self, request, **kwargs):  # pylint: disable=unused-argument
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


class EnterpriseLearnerViewSet(EnterpriseViewSet, viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise Learners.
    """
    queryset = EnterpriseLearner.objects.all()
    serializer_class = serializers.EnterpriseLearnerSerializer
    filter_backends = (filters.OrderingFilter, AuditUsersEnrollmentFilterBackend,)
    ordering_fields = '__all__'
    ordering = ('user_email',)

    def get_queryset(self):
        LOGGER.info("[ELV_ANALYTICS_API_V1] QueryParams: [%s]", self.request.query_params)
        queryset = super().get_queryset().prefetch_related(
            Prefetch(
                'enrollments',
                queryset=EnterpriseLearnerEnrollment.objects.filter(
                    enterprise_customer_uuid=self.kwargs['enterprise_id']
                )
            ),
        )

        has_enrollments = self.request.query_params.get('has_enrollments')
        if has_enrollments == 'true':
            queryset = queryset.filter(enrollments__isnull=False).distinct()
        elif has_enrollments == 'false':
            queryset = queryset.filter(enrollments__isnull=True)

        active_courses = self.request.query_params.get('active_courses')
        if active_courses == 'true':
            queryset = queryset.filter(
                Q(enrollments__is_consent_granted=True),
                enrollments__course_end_date__gte=timezone.now()
            )
        elif active_courses == 'false':
            queryset = queryset.filter(
                Q(enrollments__is_consent_granted=True),
                enrollments__course_end_date__lte=timezone.now()
            )

        all_enrollments_passed = self.request.query_params.get('all_enrollments_passed')
        if all_enrollments_passed == 'true':
            queryset = queryset.filter(enrollments__has_passed=True)
        elif all_enrollments_passed == 'false':
            queryset = queryset.filter(enrollments__has_passed=False)

        extra_fields = self.request.query_params.getlist('extra_fields')
        if 'enrollment_count' in extra_fields:
            enrollment_subquery = (
                EnterpriseLearnerEnrollment.objects.filter(
                    enterprise_user=OuterRef("enterprise_user_id"),
                    is_consent_granted=True,
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
                EnterpriseLearnerEnrollment.objects.filter(
                    enterprise_user=OuterRef("enterprise_user_id"),
                    has_passed=True,
                    is_consent_granted=True,
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

    def list(self, request, **kwargs):
        """
        List view for learner records for a given enterprise.
        """
        users = self.get_queryset().filter(enterprise_customer_uuid=kwargs['enterprise_id'])

        # do the sorting
        users = self.filter_queryset(users)
        LOGGER.info("[ELV_ANALYTICS_API_V1] QuerySet.Query: [%s]", users.query)

        # Bit to account for pagination
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class EnterpriseLearnerCompletedCoursesViewSet(EnterpriseViewSet, viewsets.ModelViewSet):
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
            return EnterpriseLearnerEnrollment.objects.none()

        # Get the number of completed courses against a learner.
        enrollments = EnterpriseLearnerEnrollment.objects.filter(
            enterprise_customer_uuid=self.kwargs['enterprise_id'],
            has_passed=True,
            is_consent_granted=True,  # DSC check required
        ).values('user_email').annotate(completed_courses=Count('courserun_key')).order_by('user_email')
        return enrollments
