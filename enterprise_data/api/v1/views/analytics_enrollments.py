"""Advance Analytics for Enrollments"""
import json
from datetime import datetime

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import StreamingHttpResponse

from enterprise_data.admin_analytics.constants import (
    CALCULATION_TOTAL,
    CSV_ENROLLMENTS_OVER_TIME,
    CSV_INDIVIDUAL_ENROLLMENTS,
    CSV_TOP_COURSES_BY_ENROLLMENTS,
    CSV_TOP_SUBJECTS_BY_ENROLLMENTS,
    GRANULARITY_DAILY,
)
from enterprise_data.admin_analytics.utils import (
    calculation_aggregation,
    fetch_and_cache_enrollments_data,
    granularity_aggregation,
)
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.api.v1.serializers import (
    AdvanceAnalyticsEnrollmentSerializer,
    AdvanceAnalyticsEnrollmentStatsSerializer,
)
from enterprise_data.renderers import IndividualEnrollmentsCSVRenderer
from enterprise_data.utils import date_filter


def fetch_enrollments_cache_expiry_timestamp():
    """Helper method to calculate cache expiry timestamp"""
    # TODO: Implement cache expiry logic
    return datetime.now()


class AdvanceAnalyticsIndividualEnrollmentsView(APIView):
    """
    API for getting the advance analytics individual enrollments data.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = AdvanceAnalyticsPagination
    http_method_names = ['get']

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def get(self, request, enterprise_uuid):
        """Get individual enrollments data"""
        serializer = AdvanceAnalyticsEnrollmentSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry)

        # get values from query params or use default values
        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        csv_type = request.query_params.get('csv_type')

        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        # select only the columns that will be in the table.
        enrollments = enrollments[
            [
                "email",
                "course_title",
                "course_subject",
                "enroll_type",
                "enterprise_enrollment_date",
            ]
        ]
        enrollments["enterprise_enrollment_date"] = enrollments["enterprise_enrollment_date"].dt.date
        enrollments = enrollments.sort_values(by="enterprise_enrollment_date", ascending=False).reset_index(drop=True)

        if csv_type == CSV_INDIVIDUAL_ENROLLMENTS:
            return StreamingHttpResponse(
                IndividualEnrollmentsCSVRenderer().render(self._stream_serialized_data(enrollments)),
                content_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="individual_enrollments.csv"'},
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(enrollments, request)
        serialized_data = page.data.to_dict(orient='records')
        response = paginator.get_paginated_response(serialized_data)

        return response

    def _stream_serialized_data(self, enrollments, chunk_size=50000):
        """
        Stream the serialized data.
        """
        total_rows = enrollments.shape[0]
        for start_index in range(0, total_rows, chunk_size):
            end_index = min(start_index + chunk_size, total_rows)
            chunk = enrollments.iloc[start_index:end_index]
            yield from chunk.to_dict(orient='records')


class AdvanceAnalyticsEnrollmentStatsView(APIView):
    """
    API for getting the advance analytics enrollment chart stats.
    """
    authentication_classes = (JwtAuthentication,)
    http_method_names = ['get']

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def get(self, request, enterprise_uuid):
        """Get enrollment chart stats"""
        serializer = AdvanceAnalyticsEnrollmentStatsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry)

        # get values from query params or use default
        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        granularity = serializer.data.get('granularity', GRANULARITY_DAILY)
        calculation = serializer.data.get('calculation', CALCULATION_TOTAL)
        csv_type = serializer.data.get('csv_type')

        data = {}
        if csv_type is None:
            data = {
                "enrollments_over_time": self.construct_enrollments_over_time(
                    enrollments_df.copy(),
                    start_date,
                    end_date,
                    granularity,
                    calculation,
                ),
                "top_courses_by_enrollments": self.construct_top_courses_by_enrollments(
                    enrollments_df.copy(),
                    start_date,
                    end_date,
                ),
                "top_subjects_by_enrollments": self.construct_top_subjects_by_enrollments(
                    enrollments_df.copy(),
                    start_date,
                    end_date,
                ),
            }
        elif csv_type == CSV_ENROLLMENTS_OVER_TIME:
            data = self.construct_enrollments_over_time_csv(
                enrollments_df.copy(),
                start_date,
                end_date,
                granularity,
                calculation,
            )
        elif csv_type == CSV_TOP_COURSES_BY_ENROLLMENTS:
            data = self.construct_top_courses_by_enrollments_csv(
                enrollments_df.copy(),
                start_date,
                end_date,
            )
        elif csv_type == CSV_TOP_SUBJECTS_BY_ENROLLMENTS:
            data = self.construct_top_subjects_by_enrollments_csv(
                enrollments_df.copy(),
                start_date,
                end_date,
            )

        return Response(data)

    def construct_enrollments_over_time(self, enrollments_df, start_date, end_date, granularity, calculation):
        """Construct enrollments over time data"""
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        # aggregate enrollments by granularity
        enrollments = granularity_aggregation(
            level=granularity,
            group=["enterprise_enrollment_date", "enroll_type"],
            date="enterprise_enrollment_date",
            data_frame=enrollments,
        )

        # aggregate enrollments by calculation
        enrollments = calculation_aggregation(calc=calculation, data_frame=enrollments)

        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_enrollments_over_time_csv(self, enrollments_df, start_date, end_date, granularity, calculation):
        """Construct enrollments over time CSV"""
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        # aggregate enrollments by granularity
        enrollments = granularity_aggregation(
            level=granularity,
            group=["enterprise_enrollment_date", "enroll_type"],
            date="enterprise_enrollment_date",
            data_frame=enrollments,
        )

        # aggregate enrollments by calculation
        enrollments = calculation_aggregation(calc=calculation, data_frame=enrollments)

        enrollments = enrollments.pivot(
            index="enterprise_enrollment_date", columns="enroll_type", values="count"
        )

        return {
            'csv_data': json.loads(enrollments.to_json(orient='table'))['data'],
            'filename': f"""Enrollment Timeseries, {start_date} - {end_date} ({granularity} {calculation}).csv"""
        }

    def construct_top_courses_by_enrollments(self, enrollments_df, start_date, end_date):
        """Construct top courses by enrollments data"""
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        courses = list(
            enrollments.groupby(["course_key"]).size().sort_values(ascending=False)[:10].index
        )

        enrollments = (
            enrollments[enrollments.course_key.isin(courses)]
            .groupby(["course_key", "enroll_type"])
            .size()
            .reset_index()
        )
        enrollments.columns = ["course_key", "enroll_type", "count"]

        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_top_courses_by_enrollments_csv(self, enrollments_df, start_date, end_date):
        """Construct top courses by enrollments CSV"""
        # Date filtering.
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        courses = list(
            enrollments.groupby(["course_key"]).size().sort_values(ascending=False)[:10].index
        )

        enrollments = (
            enrollments[enrollments.course_key.isin(courses)]
            .groupby(["course_key", "course_title", "enroll_type"])
            .size()
            .reset_index()
        )
        enrollments.columns = ["course_key", "course_title", "enroll_type", "count"]

        enrollments = enrollments.pivot(
            index=["course_key", "course_title"], columns="enroll_type", values="count"
        )

        return {
            'csv_data': json.loads(enrollments.to_json(orient='table'))['data'],
            'filename': f"""Top 10 Courses, {start_date} - {end_date}.csv"""
        }

    def construct_top_subjects_by_enrollments(self, enrollments_df, start_date, end_date):
        """Construct top subjects by enrollments data"""
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        subjects = list(
            enrollments.groupby(["course_subject"]).size().sort_values(ascending=False)[:10].index
        )

        enrollments = (
            enrollments[enrollments.course_subject.isin(subjects)]
            .groupby(["course_subject", "enroll_type"])
            .size()
            .reset_index()
        )
        enrollments.columns = ["course_subject", "enroll_type", "count"]

        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_top_subjects_by_enrollments_csv(self, enrollments_df, start_date, end_date):
        """Construct top subjects by enrollments CSV"""
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        subjects = list(
            enrollments.groupby(["course_subject"]).size().sort_values(ascending=False)[:10].index
        )

        enrollments = (
            enrollments[enrollments.course_subject.isin(subjects)]
            .groupby(["course_subject", "enroll_type"])
            .size()
            .reset_index()
        )
        enrollments.columns = ["course_subject", "enroll_type", "count"]

        enrollments = enrollments.pivot(index="course_subject", columns="enroll_type", values="count")

        return {
            'csv_data': json.loads(enrollments.to_json(orient='table'))['data'],
            'filename': f"""Top 10 Subjects by Enrollment, {start_date} - {end_date}.csv"""
        }
