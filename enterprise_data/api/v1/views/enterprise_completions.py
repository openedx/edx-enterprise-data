"""Views for enterprise admin completions analytics."""
import datetime
from datetime import datetime, timedelta

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from django.http import HttpResponse

from enterprise_data.admin_analytics.completions_utils import (
    get_completions_over_time,
    get_csv_data_for_completions_over_time,
    get_csv_data_for_top_courses_by_completions,
    get_csv_data_for_top_subjects_by_completions,
    get_top_courses_by_completions,
    get_top_subjects_by_completions,
)
from enterprise_data.admin_analytics.constants import CALCULATION, GRANULARITY
from enterprise_data.admin_analytics.data_loaders import fetch_max_enrollment_datetime
from enterprise_data.admin_analytics.utils import ChartType, fetch_and_cache_enrollments_data
from enterprise_data.api.v1 import serializers
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.utils import date_filter


class EnterrpiseAdminCompletionsStatsView(APIView):
    """
    API for getting the enterprise admin completions.
    """
    authentication_classes = (JwtAuthentication,)
    http_method_names = ['get']

    @permission_required(
        "can_access_enterprise", fn=lambda request, enterprise_id: enterprise_id
    )
    def get(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise admin completions
        """
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(
            data=request.GET
        )
        serializer.is_valid(raise_exception=True)

        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = (
            last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
        )

        enrollments = fetch_and_cache_enrollments_data(
            enterprise_id, cache_expiry
        ).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get(
            "start_date", enrollments.enterprise_enrollment_date.min()
        )
        end_date = serializer.data.get("end_date", datetime.now())

        if serializer.data.get('response_type') == 'csv':
            chart_type = serializer.data.get('chart_type')
            response = HttpResponse(content_type='text/csv')
            csv_data = {}

            if chart_type == ChartType.COMPLETIONS_OVER_TIME.value:
                csv_data = get_csv_data_for_completions_over_time(
                    start_date=start_date,
                    end_date=end_date,
                    enrollments=enrollments.copy(),
                    date_agg=serializer.data.get('granularity', GRANULARITY.DAILY.value),
                    calc=serializer.data.get('calculation', CALCULATION.TOTAL.value),
                )
            elif chart_type == ChartType.TOP_COURSES_BY_COMPLETIONS.value:
                csv_data = get_csv_data_for_top_courses_by_completions(
                    start_date=start_date, end_date=end_date, enrollments=enrollments.copy()
                )
            elif chart_type == ChartType.TOP_SUBJECTS_BY_COMPLETIONS.value:
                csv_data = get_csv_data_for_top_subjects_by_completions(
                    start_date=start_date, end_date=end_date, enrollments=enrollments.copy()
                )
            filename = csv_data['filename']
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            csv_data['data'].to_csv(path_or_buf=response)
            return response

        completions_over_time = get_completions_over_time(
            start_date=start_date,
            end_date=end_date,
            dff=enrollments.copy(),
            date_agg=serializer.data.get('granularity', GRANULARITY.DAILY.value),
            calc=serializer.data.get('calculation', CALCULATION.TOTAL.value),
        )
        top_courses_by_completions = get_top_courses_by_completions(
            start_date=start_date, end_date=end_date, dff=enrollments.copy()
        )
        top_subjects_by_completions = get_top_subjects_by_completions(
            start_date=start_date, end_date=end_date, dff=enrollments.copy()
        )

        return Response(
            data={
                'completions_over_time': completions_over_time.to_dict(
                    orient="records"
                ),
                'top_courses_by_completions': top_courses_by_completions.to_dict(
                    orient="records"
                ),
                'top_subjects_by_completions': top_subjects_by_completions.to_dict(
                    orient="records"
                ),
            },
            status=HTTP_200_OK,
        )


class EnterrpiseAdminCompletionsView(APIView):
    """
    API for getting the enterprise admin completions.
    """
    authentication_classes = (JwtAuthentication,)
    http_method_names = ['get']
    pagination_class = AdvanceAnalyticsPagination

    @permission_required(
        "can_access_enterprise", fn=lambda request, enterprise_id: enterprise_id
    )
    def get(self, request, enterprise_id):
        """
        HTTP GET endpoint to retrieve the enterprise admin completions
        """
        serializer = serializers.AdminAnalyticsAggregatesQueryParamsSerializer(
            data=request.GET
        )
        serializer.is_valid(raise_exception=True)

        last_updated_at = fetch_max_enrollment_datetime()
        cache_expiry = (
            last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
        )

        enrollments = fetch_and_cache_enrollments_data(
            enterprise_id, cache_expiry
        ).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get(
            'start_date', enrollments.enterprise_enrollment_date.min()
        )
        end_date = serializer.data.get('end_date', datetime.now())

        dff = enrollments[enrollments['has_passed'] == 1]

        # Date filtering
        dff = date_filter(start=start_date, end=end_date, data_frame=dff, date_column='passed_date')

        dff = dff[['email', 'course_title', 'course_subject', 'passed_date']]
        dff['passed_date'] = dff['passed_date'].dt.date
        dff = dff.sort_values(by="passed_date", ascending=False).reset_index(drop=True)

        if serializer.data.get('response_type') == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"Individual Completions, {start_date} - {end_date}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            dff.to_csv(path_or_buf=response, index=False)
            return response

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dff, request)
        serialized_data = page.data.to_dict(orient='records')
        response = paginator.get_paginated_response(serialized_data)

        return response
