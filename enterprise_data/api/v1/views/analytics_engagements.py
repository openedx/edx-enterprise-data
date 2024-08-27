"""Advance Analytics for Engagements"""
from datetime import datetime

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status as rest_status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import HttpResponse, StreamingHttpResponse

from enterprise_data.admin_analytics.constants import Calculation, EngagementChart, Granularity, ResponseType
from enterprise_data.admin_analytics.utils import (
    calculation_aggregation,
    fetch_and_cache_engagements_data,
    fetch_and_cache_enrollments_data,
    fetch_enrollments_cache_expiry_timestamp,
    granularity_aggregation,
)
from enterprise_data.api.v1 import serializers
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.renderers import IndividualEngagementsCSVRenderer
from enterprise_data.utils import date_filter


class AdvanceAnalyticsIndividualEngagementsView(APIView):
    """
    API for getting the advance analytics individual engagements data.
    """

    authentication_classes = (JwtAuthentication,)
    pagination_class = AdvanceAnalyticsPagination
    http_method_names = ["get"]

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def get(self, request, enterprise_uuid):
        """
        HTTP GET endpoint to retrieve the enterprise engagements data.
        """
        serializer = serializers.AdvanceAnalyticsEngagementStatsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        cache_expiry = fetch_enrollments_cache_expiry_timestamp()

        enrollment_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry).copy()
        engagement_df = fetch_and_cache_engagements_data(enterprise_uuid, cache_expiry).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get('start_date', enrollment_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        response_type = request.query_params.get('response_type', ResponseType.JSON.value)
        # Date filtering.
        engagements = date_filter(
            start=start_date, end=end_date, data_frame=engagement_df.copy(), date_column='activity_date'
        )
        engagements["learning_time_hours"] = engagements["learning_time_seconds"] / 60 / 60
        engagements = engagements[engagements["learning_time_hours"] > 0]
        engagements["learning_time_hours"] = round(engagements["learning_time_hours"].astype(float), 1)

        # Select only the columns that will be in the table.
        engagements = engagements[
            [
                "email",
                "course_title",
                "activity_date",
                "course_subject",
                "learning_time_hours",
            ]
        ]
        engagements["activity_date"] = engagements["activity_date"].dt.date
        engagements = engagements.sort_values(by="activity_date", ascending=False).reset_index(drop=True)
        if response_type == ResponseType.CSV.value:
            response = StreamingHttpResponse(
                IndividualEngagementsCSVRenderer().render(self._stream_serialized_data(engagements)),
                content_type="text/csv"
            )
            start_date = start_date.strftime('%Y/%m/%d')
            end_date = end_date.strftime('%Y/%m/%d')
            filename = f"""Individual Engagements, {start_date} - {end_date}.csv"""
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(engagements, request)
        serialized_data = page.data.to_dict(orient='records')
        response = paginator.get_paginated_response(serialized_data)

        return response

    def _stream_serialized_data(self, engagements, chunk_size=50000):
        """
        Stream the serialized data.
        """
        total_rows = engagements.shape[0]
        for start_index in range(0, total_rows, chunk_size):
            end_index = min(start_index + chunk_size, total_rows)
            chunk = engagements.iloc[start_index:end_index]
            yield from chunk.to_dict(orient='records')


class AdvanceAnalyticsEngagementStatsView(APIView):
    """
    API for getting the advance analytics engagements statistics data.
    """

    authentication_classes = (JwtAuthentication,)
    http_method_names = ["get"]

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def get(self, request, enterprise_uuid):
        """
        HTTP GET endpoint to retrieve the enterprise engagements statistics data.
        """
        serializer = serializers.AdvanceAnalyticsEngagementStatsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()

        enrollment_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry).copy()
        engagement_df = fetch_and_cache_engagements_data(enterprise_uuid, cache_expiry).copy()
        # Use start and end date if provided by the client, if client has not provided then use
        # 1. minimum enrollment date from the data as the start_date
        # 2. today's date as the end_date
        start_date = serializer.data.get('start_date', enrollment_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        granularity = serializer.data.get('granularity', Granularity.DAILY.value)
        calculation = serializer.data.get('calculation', Calculation.TOTAL.value)
        chart_type = serializer.data.get('chart_type')

        if chart_type is None:
            data = {
                "engagements_over_time": self.construct_engagements_over_time(
                    engagement_df.copy(),
                    start_date,
                    end_date,
                    granularity,
                    calculation,
                ),
                "top_courses_by_engagement": self.construct_top_courses_by_engagements(
                    engagement_df.copy(),
                    start_date,
                    end_date,
                ),
                "top_subjects_by_engagement": self.construct_top_subjects_by_engagements(
                    engagement_df.copy(),
                    start_date,
                    end_date,
                ),
            }
            return Response(data)
        elif chart_type == EngagementChart.ENGAGEMENTS_OVER_TIME.value:
            return self.construct_engagements_over_time_csv(
                engagement_df.copy(),
                start_date,
                end_date,
                granularity,
                calculation,
            )
        elif chart_type == EngagementChart.TOP_COURSES_BY_ENGAGEMENTS.value:
            return self.construct_top_courses_by_engagements_csv(
                engagement_df.copy(),
                start_date,
                end_date,
            )
        elif chart_type == EngagementChart.TOP_SUBJECTS_BY_ENGAGEMENTS.value:
            return self.construct_top_subjects_by_engagements_csv(
                engagement_df.copy(),
                start_date,
                end_date,
            )
        return Response(data='Not Found', status=rest_status.HTTP_400_BAD_REQUEST)

    def engagements_over_time_common(self, engagements_df, start_date, end_date, granularity, calculation):
        """
        Common method for constructing engagements over time data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
        engagements_df["learning_time_hours"] = engagements_df["learning_time_seconds"] / 60 / 60
        engagements_df = engagements_df[engagements_df["learning_time_hours"] > 0]
        engagements_df["learning_time_hours"] = round(engagements_df["learning_time_hours"].astype(float), 1)

        engagements_df = engagements_df[["activity_date", "enroll_type", "learning_time_hours"]]

        # Date filtering.
        engagements_df = date_filter(
            start=start_date, end=end_date, data_frame=engagements_df, date_column="activity_date"
        )

        # Date aggregation.
        engagements_df = granularity_aggregation(
            level=granularity,
            group=["activity_date", "enroll_type"],
            date="activity_date",
            data_frame=engagements_df,
            aggregation_type="sum",
        )

        # Calculating metric.
        engagements = calculation_aggregation(calc=calculation, aggregation_type="sum", data_frame=engagements_df)
        return engagements

    def construct_engagements_over_time(self, engagements_df, start_date, end_date, granularity, calculation):
        """
        Construct engagements over time data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
        engagements = self.engagements_over_time_common(engagements_df, start_date, end_date, granularity, calculation)
        # convert dataframe to a list of records
        return engagements.to_dict(orient='records')

    def construct_engagements_over_time_csv(self, engagements_df, start_date, end_date, granularity, calculation):
        """
        Construct engagements over time CSV.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
        engagements = self.engagements_over_time_common(engagements_df, start_date, end_date, granularity, calculation)

        engagements = engagements.pivot(
            index="activity_date", columns="enroll_type", values="sum"
        )

        filename = f"Engagement Timeseries, {start_date} - {end_date} ({granularity} {calculation}).csv"
        return self.construct_csv_response(engagements, filename)

    def top_courses_by_engagements_common(self, engagements_df, start_date, end_date):
        """
        Common method for constructing top courses by engagements data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
            group_by_columns {list} -- List of columns to group by
            columns {list} -- List of column for the final result
        """
        engagements_df["learning_time_hours"] = engagements_df["learning_time_seconds"] / 60 / 60
        engagements_df["learning_time_hours"] = engagements_df["learning_time_hours"].astype("float")

        # Date filtering.
        engagements = date_filter(
            start=start_date, end=end_date, data_frame=engagements_df, date_column="activity_date"
        )

        courses = list(
            engagements.groupby(["course_key"])
            .learning_time_hours.sum()
            .sort_values(ascending=False)[:10]
            .index
        )

        engagements = (
            engagements_df[engagements_df.course_key.isin(courses)]
            .groupby(["course_key", "course_title", "enroll_type"])
            .learning_time_hours.sum()
            .reset_index()
        )

        engagements.columns = ["course_key", "course_title", "enroll_type", "count"]

        return engagements

    def construct_top_courses_by_engagements(self, engagements_df, start_date, end_date):
        """
        Construct top courses by engagements data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
        """
        engagements = self.top_courses_by_engagements_common(
            engagements_df,
            start_date,
            end_date
        )

        # convert dataframe to a list of records
        return engagements.to_dict(orient='records')

    def construct_top_courses_by_engagements_csv(self, engagements_df, start_date, end_date):
        """
        Construct top courses by engagements CSV.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
        """
        engagements = self.top_courses_by_engagements_common(
            engagements_df,
            start_date,
            end_date
        )

        engagements = engagements.pivot(
            index=["course_key", "course_title"], columns="enroll_type", values="count"
        )

        filename = f"Top 10 Courses by Learning Hours, {start_date} - {end_date}.csv"
        return self.construct_csv_response(engagements, filename)

    def top_subjects_by_engagements_common(self, engagements_df, start_date, end_date):
        """
        Common method for constructing top subjects by engagements data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
        """
        engagements_df["learning_time_hours"] = engagements_df["learning_time_seconds"] / 60 / 60
        engagements_df["learning_time_hours"] = engagements_df["learning_time_hours"].astype("float")

        # Date filtering.
        engagements = date_filter(
            start=start_date, end=end_date, data_frame=engagements_df, date_column="activity_date"
        )

        subjects = list(
            engagements.groupby(["course_subject"])
            .learning_time_hours.sum()
            .sort_values(ascending=False)[:10]
            .index
        )

        engagements = (
            engagements[engagements.course_subject.isin(subjects)]
            .groupby(["course_subject", "enroll_type"])
            .learning_time_hours.sum()
            .reset_index()
        )
        engagements.columns = ["course_subject", "enroll_type", "count"]

        return engagements

    def construct_top_subjects_by_engagements(self, engagements_df, start_date, end_date):
        """
        Construct top subjects by engagements data.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
        """
        engagements = self.top_subjects_by_engagements_common(engagements_df, start_date, end_date)
        # convert dataframe to a list of records
        return engagements.to_dict(orient='records')

    def construct_top_subjects_by_engagements_csv(self, engagements_df, start_date, end_date):
        """
        Construct top subjects by engagements CSV.

        Arguments:
            engagements_df {DataFrame} -- DataFrame of engagements
            start_date {datetime} -- Engagement start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Engagement end date in the format 'YYYY-MM-DD'
        """
        engagements = self.top_subjects_by_engagements_common(engagements_df, start_date, end_date)
        engagements = engagements.pivot(index="course_subject", columns="enroll_type", values="count")
        filename = f"Top 10 Subjects by Learning Hours, {start_date} - {end_date}.csv"
        return self.construct_csv_response(engagements, filename)

    def construct_csv_response(self, engagements, filename):
        """
        Construct CSV response.

        Arguments:
            engagements {DataFrame} -- DataFrame of engagements
            filename {str} -- Filename for the CSV
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        engagements.to_csv(path_or_buf=response)

        return response
