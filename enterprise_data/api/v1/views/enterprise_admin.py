"""
Views for enterprise admin api v1.
"""
import json

from datetime import datetime, timedelta

from django.http import HttpResponse, JsonResponse

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from django.http import HttpResponse

from enterprise_data.admin_analytics.data_loaders import fetch_max_enrollment_datetime
from enterprise_data.admin_analytics.utils import (
    ChartType,
    fetch_and_cache_engagements_data,
    fetch_and_cache_enrollments_data,
    date_aggregation,
    calculation
    fetch_and_cache_skills_data,
    get_skills_chart_data,
    get_top_skills_csv_data,
)
from enterprise_data.api.v1 import serializers
from enterprise_data.models import EnterpriseAdminLearnerProgress, EnterpriseAdminSummarizeInsights
from enterprise_data.utils import date_filter
from enterprise_data.paginators import ListPaginator


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

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_id: enterprise_id)
    @action(methods=['get'], detail=True)
    def enrollments(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise enrollments data.
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
        engagement = fetch_and_cache_engagements_data(
            enterprise_id, cache_expiry
        ).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get(
            "start_date", enrollment.enterprise_enrollment_date.min()
        )
        end_date = serializer.data.get("end_date", datetime.now())

        # Date filtering.
        dff = date_filter(
            start=start_date,
            end=end_date,
            data_frame=enrollment.copy(),
            date_column="enterprise_enrollment_date",
        )

        enrolls = len(dff)
        courses = len(dff.course_key.unique())

        dff = date_filter(
            start=start_date,
            end=end_date,
            data_frame=enrollment.copy(),
            date_column="passed_date",
        )

        completions = dff.has_passed.sum()

        # Date filtering.
        dff = date_filter(
            start=start_date,
            end=end_date,
            data_frame=engagement.copy(),
            date_column="activity_date",
        )

        hours = round(dff.learning_time_seconds.sum() / 60 / 60, 1)
        sessions = dff.is_engaged.sum()

        return Response(
            data={
                "enrolls": enrolls,
                "courses": courses,
                "completions": completions,
                "hours": hours,
                "sessions": sessions,
                "last_updated_at": last_updated_at.date() if last_updated_at else None,
                "min_enrollment_date": enrollment.enterprise_enrollment_date.min().date(),
                "max_enrollment_date": enrollment.enterprise_enrollment_date.max().date(),
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

        start_date = serializer.data.get("start_date")
        end_date = serializer.data.get("end_date", datetime.now())

        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = (
            last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
        )
        skills = fetch_and_cache_skills_data(enterprise_id, cache_expiry).copy()

        if request.GET.get("format") == "csv":
            csv_data = get_top_skills_csv_data(skills, start_date, end_date)
            response = HttpResponse(content_type='text/csv')
            filename = f"Skills by Enrollment and Completion, {start_date} - {end_date}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            csv_data.to_csv(path_or_buf=response, index=False)
            return response

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


    @permission_required('can_access_enterprise', fn=lambda request, enterprise_id: enterprise_id)
    @action(methods=['get'], detail=False)
    def engagements(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise engagements data.
        """
        paginator = ListPaginator(request=request)
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()

        enrollment = fetch_and_cache_enrollments_data(enterprise_id, cache_expiry).copy()
        engagement = fetch_and_cache_engagements_data(enterprise_id, cache_expiry).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get('start_date', enrollment.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        # Date filtering.
        dff = date_filter(
            start=start_date, end=end_date, data_frame=engagement.copy(), date_column='activity_date'
        )
        dff["learning_time_hours"] = dff["learning_time_seconds"] / 60 / 60
        dff = dff[dff["learning_time_hours"] > 0]
        dff["learning_time_hours"] = round(dff["learning_time_hours"].astype(float), 1)

         # Select only the columns that will be in the table.
        dff = dff[
            [
                "email",
                "course_title",
                "activity_date",
                "course_subject",
                "learning_time_hours",
            ]
        ]
        dff["activity_date"] = dff["activity_date"].dt.date
        dff = dff.sort_values(by="activity_date", ascending=False).reset_index(drop=True)
        response_type = serializer.data.get('response_type')
        if response_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"""Individual Engagements, {start_date} - {end_date}.csv"""
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            dff.to_csv(path_or_buf=response, index=False)
            return response
        else:
            response_data = dff.to_dict(orient='records')
            return paginator.paginate_list(data=response_data, page_number=serializer.data.get('page'))


    def _get_engagements_over_time(engagement, start_date, end_date, date_agg, calc):
        dff = engagement.copy()
        dff["learning_time_hours"] = dff["learning_time_seconds"] / 60 / 60
        dff = dff[dff["learning_time_hours"] > 0]
        dff["learning_time_hours"] = round(dff["learning_time_hours"].astype(float), 1)

        dff = dff[["activity_date", "enroll_type", "learning_time_hours"]]

        # Date filtering.
        dff = date_filter(start=start_date, end=end_date, df=dff, date="activity_date")

        # Date aggregation.
        dff = date_aggregation(
            level=date_agg,
            group=["activity_date", "enroll_type"],
            date="activity_date",
            df=dff,
            type_="sum",
        )

        # Calculating metric.
        dff = calculation(calc=calc, val="sum", df=dff)
        dff = dff.pivot(index="activity_date", columns="enroll_type", values="sum")
        return dff.to_dict('records')
    

    def _get_top_courses_by_engagement(engagement, start_date, end_date):
        dff = engagement.copy()
        dff["learning_time_hours"] = dff["learning_time_seconds"] / 60 / 60

        # Date filtering.
        dff = date_filter(start=start_date, end=end_date, df=dff, date="activity_date")

        courses = list(
            dff.groupby(["course_key"])
            .learning_time_hours.sum()
            .sort_values(ascending=False)[:10]
            .index
        )

        dff = (
            dff[dff.course_key.isin(courses)]
            .groupby(["course_key", "course_title", "enroll_type"])
            .learning_time_hours.sum()
            .reset_index()
        )
        dff.columns = ["course_key", "course_title", "enroll_type", "count"]

        dff = dff.pivot(
            index=["course_key", "course_title"], columns="enroll_type", values="count"
        )
        return dff.to_dict('records')


    def _get_top_subjects_by_engagement(engagement, start_date, end_date):
        dff = engagement.copy()
        dff["learning_time_hours"] = dff["learning_time_seconds"] / 60 / 60

        # Date filtering.
        dff = date_filter(start=start_date, end=end_date, df=dff, date="activity_date")

        subjects = list(
            dff.groupby(["course_subject"])
            .learning_time_hours.sum()
            .sort_values(ascending=False)[:10]
            .index
        )

        dff = (
            dff[dff.course_subject.isin(subjects)]
            .groupby(["course_subject", "enroll_type"])
            .learning_time_hours.sum()
            .reset_index()
        )
        dff.columns = ["course_subject", "enroll_type", "count"]

        dff = dff.pivot(index="course_subject", columns="enroll_type", values="count")
        return dff.to_dict('records')


    @permission_required('can_access_enterprise', fn=lambda request, enterprise_id: enterprise_id)
    @action(methods=['get'], detail=False, url_path='engagements/stats)')
    def get_engagements_stats(self, request, enterprise_id):
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()

        enrollment = fetch_and_cache_enrollments_data(enterprise_id, cache_expiry).copy()
        engagement = fetch_and_cache_engagements_data(enterprise_id, cache_expiry).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get('start_date', enrollment.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())

        engagements_over_time = self._get_engagements_over_time(
            engagement,
            start_date,
            end_date,
            serializer.data.get('date_agg'),
            serializer.data.get('calc')
        )
        top_courses_by_engagement = self._get_top_courses_by_engagement(
            engagement,
            start_date,
            end_date
        )
        top_subjects_by_engagement = self._get_top_subjects_by_engagement(
            engagement,
            start_date,
            end_date
        )
        response_data = {
            "engagement_over_time": engagements_over_time,
            "top_courses_by_engagement": top_courses_by_engagement,
            "top_subjects_by_engagement": top_subjects_by_engagement
        }
        return JsonResponse(response_data, status=200, safe=False)
