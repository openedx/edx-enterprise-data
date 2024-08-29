"""
Views for enterprise admin api v1.
"""
from datetime import datetime, timedelta

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import filters, viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from django.http import HttpResponse

from enterprise_data.admin_analytics.data_loaders import fetch_max_enrollment_datetime
from enterprise_data.admin_analytics.database.tables import FactEngagementAdminDashTable, FactEnrollmentAdminDashTable
from enterprise_data.admin_analytics.utils import (
    ChartType,
    fetch_and_cache_enrollments_data,
    fetch_and_cache_skills_data,
    get_skills_chart_data,
    get_top_skills_csv_data,
)
from enterprise_data.api.v1 import serializers
from enterprise_data.models import (
    EnterpriseAdminLearnerProgress,
    EnterpriseAdminSummarizeInsights,
    EnterpriseExecEdLCModulePerformance,
)
from enterprise_data.utils import timer

from .base import EnterpriseViewSetMixin


class EnterpriseAdminInsightsView(APIView):
    """
    API for getting the enterprise admin insights.
    """

    authentication_classes = (JwtAuthentication,)
    http_method_names = ["get"]

    @permission_required(
        "can_access_enterprise", fn=lambda request, enterprise_id: enterprise_id
    )
    def get(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise admin insights
        """
        response_data = {}
        learner_progress = {}
        learner_engagement = {}

        try:
            learner_progress = EnterpriseAdminLearnerProgress.objects.get(
                enterprise_customer_uuid=enterprise_id
            )
            learner_progress = serializers.EnterpriseAdminLearnerProgressSerializer(
                learner_progress
            ).data
            response_data["learner_progress"] = learner_progress
        except EnterpriseAdminLearnerProgress.DoesNotExist:
            pass

        try:
            learner_engagement = EnterpriseAdminSummarizeInsights.objects.get(
                enterprise_customer_uuid=enterprise_id
            )
            learner_engagement = serializers.EnterpriseAdminSummarizeInsightsSerializer(
                learner_engagement
            ).data
            response_data["learner_engagement"] = learner_engagement
        except EnterpriseAdminSummarizeInsights.DoesNotExist:
            pass

        status = HTTP_200_OK
        if learner_progress == {} and learner_engagement == {}:
            status = HTTP_404_NOT_FOUND

        return Response(data=response_data, status=status)


class EnterpriseAdminAnalyticsAggregatesView(APIView):
    """
    API for getting the enterprise admin analytics aggregates.
    """

    authentication_classes = (JwtAuthentication,)
    http_method_names = ["get"]

    @permission_required(
        "can_access_enterprise", fn=lambda request, enterprise_id: enterprise_id
    )
    def get(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise admin aggregate data.
        """
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(
            data=request.GET
        )
        serializer.is_valid(raise_exception=True)

        last_updated_at = fetch_max_enrollment_datetime()
        min_enrollment_date, max_enrollment_date = FactEnrollmentAdminDashTable().get_enrollment_date_range(
            enterprise_id,
        )

        start_date = serializer.data.get(
            'start_date', min_enrollment_date.date()
        )
        end_date = serializer.data.get('end_date', datetime.today())

        enrolls, courses = FactEnrollmentAdminDashTable().get_enrollment_and_course_count(
            enterprise_id, start_date, end_date,
        )
        completions = FactEnrollmentAdminDashTable().get_completion_count(
            enterprise_id, start_date, end_date,
        )
        hours, sessions = FactEngagementAdminDashTable().get_learning_hours_and_daily_sessions(
            enterprise_id, start_date, end_date,
        )

        return Response(
            data={
                'enrolls': enrolls,
                'courses': courses,
                'completions': completions,
                'hours': hours,
                'sessions': sessions,
                'last_updated_at': last_updated_at.date() if last_updated_at else None,
                'min_enrollment_date': min_enrollment_date.date(),
                'max_enrollment_date': max_enrollment_date.date(),
            },
            status=HTTP_200_OK,
        )


class EnterpriseAdminAnalyticsSkillsView(APIView):
    """
    API for getting the enterprise admin analytics skills data.
    """
    authentication_classes = (JwtAuthentication,)
    http_method_names = ['get']

    @permission_required(
        'can_access_enterprise', fn=lambda request, enterprise_id: enterprise_id
    )
    def get(self, request, enterprise_id):
        """HTTP GET endpoint to retrieve the enterprise admin skills aggregated data.

        Args:
            request (HttpRequest): request object
            enterprise_id (str): UUID of the enterprise customer

        Returns:
            response(HttpResponse): response object
        """
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(
            data=request.GET
        )
        serializer.is_valid(raise_exception=True)
        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = (
            last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
        )

        enrollment = fetch_and_cache_enrollments_data(
            enterprise_id, cache_expiry
        ).copy()

        start_date = serializer.data.get('start_date', enrollment.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())

        skills = fetch_and_cache_skills_data(enterprise_id, cache_expiry).copy()

        if serializer.data.get('response_type') == 'csv':
            csv_data = get_top_skills_csv_data(skills, start_date, end_date)
            response = HttpResponse(content_type='text/csv')
            filename = f"Skills by Enrollment and Completion, {start_date} - {end_date}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            csv_data.to_csv(path_or_buf=response, index=False)
            return response

        with timer('skills_all_charts_data'):
            top_skills = get_skills_chart_data(
                chart_type=ChartType.BUBBLE,
                start_date=start_date,
                end_date=end_date,
                skills=skills,
            )
            top_skills_enrollments = get_skills_chart_data(
                chart_type=ChartType.TOP_SKILLS_ENROLLMENT,
                start_date=start_date,
                end_date=end_date,
                skills=skills,
            )
            top_skills_by_completions = get_skills_chart_data(
                chart_type=ChartType.TOP_SKILLS_COMPLETION,
                start_date=start_date,
                end_date=end_date,
                skills=skills,
            )

        response_data = {
            "top_skills": top_skills.to_dict(orient="records"),
            "top_skills_by_enrollments": top_skills_enrollments.to_dict(
                orient="records"
            ),
            "top_skills_by_completions": top_skills_by_completions.to_dict(
                orient="records"
            ),
        }

        return Response(data=response_data, status=HTTP_200_OK)


class EnterpriseExecEdLCModulePerformanceViewSet(EnterpriseViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    View to for getting enterprise exec ed learner module performance records.
    """
    serializer_class = serializers.EnterpriseExecEdLCModulePerformanceSerializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = '__all__'
    ordering = ('last_access',)
    search_fields = (
        'username',
        'course_name'
    )

    def get_queryset(self):
        """
        Return the queryset of EnterpriseExecEdLCModulePerformance objects.
        """
        return EnterpriseExecEdLCModulePerformance.objects.filter(
            enterprise_customer_uuid=self.kwargs['enterprise_id'],
        )
