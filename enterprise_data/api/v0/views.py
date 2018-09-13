# -*- coding: utf-8 -*-
"""
Views for enterprise api version 0 endpoint.
"""
from __future__ import absolute_import, unicode_literals

from datetime import date, timedelta
from logging import getLogger

from edx_rest_framework_extensions.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import filters, viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from django.db.models import Count, Max
from django.utils import timezone

from enterprise_data.api.v0 import serializers
from enterprise_data.filters import ConsentGrantedFilterBackend
from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser
from enterprise_data.permissions import HasDataAPIDjangoGroupAccess

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


class EnterpriseViewSet(viewsets.ViewSet):
    """
    Base class for all Enterprise view sets.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = DefaultPagination
    permission_classes = (HasDataAPIDjangoGroupAccess,)

    def ensure_data_exists(self, request, data, error_message=None):
        """
        Ensure that the API response brings us valid data. If not, raise an error and log it.
        """
        if not data:
            error_message = (
                error_message or "Unable to fetch API response from endpoint '{}'.".format(request.get_full_path())
            )
            LOGGER.error(error_message)
            raise NotFound(error_message)

    def paginate_queryset(self, queryset):
        """
        Allows no_page query param to skip pagination
        """
        if 'no_page' in self.request.query_params:
            return None
        return super(EnterpriseViewSet, self).paginate_queryset(queryset)


class EnterpriseEnrollmentsViewSet(EnterpriseViewSet, viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise course enrollments.
    """
    serializer_class = serializers.EnterpriseEnrollmentSerializer
    filter_backends = (ConsentGrantedFilterBackend, filters.OrderingFilter,)
    ordering_fields = '__all__'
    ordering = ('user_email',)
    CONSENT_GRANTED_FILTER = 'consent_granted'

    def get_queryset(self):
        """
        Returns all learner enrollment records for a given enterprise.
        """
        enterprise_id = self.kwargs['enterprise_id']
        enrollments = EnterpriseEnrollment.objects.filter(enterprise_id=enterprise_id)

        enrollments = self.apply_filters(enrollments)

        self.ensure_data_exists(
            self.request,
            enrollments,
            error_message=(
                "No course enrollments are associated with Enterprise {enterprise_id} from endpoint '{path}'."
                .format(
                    enterprise_id=enterprise_id,
                    path=self.request.get_full_path()
                )
            )
        )
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
        if learner_activity_param == 'active_past_week':
            queryset = self.filter_active_learners(queryset, past_week_date)
        elif learner_activity_param == 'inactive_past_week':
            queryset = self.filter_inactive_learners(queryset, past_week_date)
        elif learner_activity_param == 'inactive_past_month':
            queryset = self.filter_inactive_learners(queryset, past_month_date)

        return queryset

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
        date_today = date.today()
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

    @list_route()
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


class EnterpriseUsersViewSet(EnterpriseViewSet, viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise users.
    """
    queryset = EnterpriseUser.objects.all()
    serializer_class = serializers.EnterpriseUserSerializer

    def list(self, request, **kwargs):
        """
        List view for learner records for a given enterprise.
        """
        enterprise_id = kwargs['enterprise_id']
        users = self.queryset.filter(enterprise_id=enterprise_id)

        has_enrollments = request.query_params.get('has_enrollments')
        if has_enrollments == 'true':
            users = users.filter(enrollments__isnull=False).distinct()
        elif has_enrollments == 'false':
            users = users.filter(enrollments__isnull=True)

        active_courses = request.query_params.get('active_courses')
        if active_courses == 'true':
            users = users.filter(enrollments__course_end__gte=timezone.now())
        elif active_courses == 'false':
            users = users.filter(enrollments__course_end__lte=timezone.now())

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

    def get_queryset(self):
        """
        Returns number of completed courses against each learner.
        """
        enterprise_id = self.kwargs['enterprise_id']
        # Get the number of completed courses against a learner.
        enrollments = EnterpriseEnrollment.objects.filter(
            enterprise_id=enterprise_id,
            has_passed=True
        ).values('user_email').annotate(completed_courses=Count('course_id')).order_by('user_email')
        return enrollments
