"""Advance Analytics for Enrollments"""
from datetime import datetime
from logging import getLogger

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import HttpResponse, StreamingHttpResponse

from enterprise_data.admin_analytics.constants import Calculation, EnrollmentChart, Granularity, ResponseType
from enterprise_data.admin_analytics.utils import (
    calculation_aggregation,
    fetch_and_cache_enrollments_data,
    fetch_enrollments_cache_expiry_timestamp,
    granularity_aggregation,
)
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.api.v1.serializers import (
    AdvanceAnalyticsEnrollmentStatsSerializer,
    AdvanceAnalyticsQueryParamSerializer,
)
from enterprise_data.renderers import IndividualEnrollmentsCSVRenderer
from enterprise_data.utils import date_filter, timer

LOGGER = getLogger(__name__)


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
        serializer = AdvanceAnalyticsQueryParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry)

        # get values from query params or use default values
        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        response_type = request.query_params.get('response_type', ResponseType.JSON.value)

        LOGGER.info(
            "Individual enrollments data requested for enterprise [%s] from [%s] to [%s]",
            enterprise_uuid,
            start_date,
            end_date,
        )

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

        LOGGER.info(
            "Individual enrollments data prepared for enterprise [%s] from [%s] to [%s]",
            enterprise_uuid,
            start_date,
            end_date,
        )

        if response_type == ResponseType.CSV.value:
            filename = f"""individual_enrollments, {start_date} - {end_date}.csv"""
            return StreamingHttpResponse(
                IndividualEnrollmentsCSVRenderer().render(self._stream_serialized_data(enrollments)),
                content_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
    def get(self, request, enterprise_uuid):  # lint-amnesty, pylint: disable=inconsistent-return-statements
        """Get enrollment chart stats"""
        serializer = AdvanceAnalyticsEnrollmentStatsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry)

        # get values from query params or use default
        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        granularity = serializer.data.get('granularity', Granularity.DAILY.value)
        calculation = serializer.data.get('calculation', Calculation.TOTAL.value)
        response_type = serializer.data.get('response_type', ResponseType.JSON.value)
        chart_type = serializer.data.get('chart_type')

        # TODO: Add validation that if response_type is CSV then chart_type must be provided

        if response_type == ResponseType.JSON.value:
            with timer('construct_enrollment_all_stats'):
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
            return Response(data)

        if response_type == ResponseType.CSV.value:
            if chart_type == EnrollmentChart.ENROLLMENTS_OVER_TIME.value:
                with timer('construct_enrollments_over_time_csv'):
                    return self.construct_enrollments_over_time_csv(
                        enrollments_df.copy(),
                        start_date,
                        end_date,
                        granularity,
                        calculation,
                    )
            elif chart_type == EnrollmentChart.TOP_COURSES_BY_ENROLLMENTS.value:
                with timer('construct_top_courses_by_enrollments_csv'):
                    return self.construct_top_courses_by_enrollments_csv(
                        enrollments_df.copy(),
                        start_date,
                        end_date,
                    )
            elif chart_type == EnrollmentChart.TOP_SUBJECTS_BY_ENROLLMENTS.value:
                with timer('construct_top_subjects_by_enrollments_csv'):
                    return self.construct_top_subjects_by_enrollments_csv(
                        enrollments_df.copy(),
                        start_date,
                        end_date,
                    )

    def enrollments_over_time_common(self, enrollments_df, start_date, end_date, granularity, calculation):
        """
        Common method for constructing enrollments over time data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
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

        return enrollments

    def construct_enrollments_over_time(self, enrollments_df, start_date, end_date, granularity, calculation):
        """
        Construct enrollments over time data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
        enrollments = self.enrollments_over_time_common(enrollments_df, start_date, end_date, granularity, calculation)

        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_enrollments_over_time_csv(self, enrollments_df, start_date, end_date, granularity, calculation):
        """
        Construct enrollments over time CSV.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
            granularity {str} -- Granularity of the data. One of Granularity choices
            calculation {str} -- Calculation of the data. One of Calculation choices
        """
        enrollments = self.enrollments_over_time_common(enrollments_df, start_date, end_date, granularity, calculation)

        enrollments = enrollments.pivot(
            index="enterprise_enrollment_date", columns="enroll_type", values="count"
        )

        filename = f"Enrollment Timeseries, {start_date} - {end_date} ({granularity} {calculation}).csv"
        return self.construct_csv_response(enrollments, filename)

    def top_courses_by_enrollments_common(self, enrollments_df, start_date, end_date, group_by_columns, columns):
        """
        Common method for constructing top courses by enrollments data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
            group_by_columns {list} -- List of columns to group by
            columns {list} -- List of column for the final result
        """
        # filter enrollments by date
        enrollments = date_filter(start_date, end_date, enrollments_df, "enterprise_enrollment_date")

        courses = list(
            enrollments.groupby(["course_key"]).size().sort_values(ascending=False)[:10].index
        )

        enrollments = (
            enrollments[enrollments.course_key.isin(courses)]
            .groupby(group_by_columns)
            .size()
            .reset_index()
        )
        enrollments.columns = columns

        return enrollments

    def construct_top_courses_by_enrollments(self, enrollments_df, start_date, end_date):
        """
        Construct top courses by enrollments data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
        """
        group_by_columns = ["course_key", "enroll_type"]
        columns = ["course_key", "enroll_type", "count"]
        enrollments = self.top_courses_by_enrollments_common(
            enrollments_df,
            start_date,
            end_date,
            group_by_columns,
            columns
        )

        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_top_courses_by_enrollments_csv(self, enrollments_df, start_date, end_date):
        """
        Construct top courses by enrollments CSV.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
        """
        group_by_columns = ["course_key", "course_title", "enroll_type"]
        columns = ["course_key", "course_title", "enroll_type", "count"]
        enrollments = self.top_courses_by_enrollments_common(
            enrollments_df,
            start_date,
            end_date,
            group_by_columns,
            columns
        )

        enrollments = enrollments.pivot(
            index=["course_key", "course_title"], columns="enroll_type", values="count"
        )

        filename = f"Top 10 Courses, {start_date} - {end_date}.csv"
        return self.construct_csv_response(enrollments, filename)

    def top_subjects_by_enrollments_common(self, enrollments_df, start_date, end_date):
        """
        Common method for constructing top subjects by enrollments data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
        """
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

        return enrollments

    def construct_top_subjects_by_enrollments(self, enrollments_df, start_date, end_date):
        """
        Construct top subjects by enrollments data.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
        """
        enrollments = self.top_subjects_by_enrollments_common(enrollments_df, start_date, end_date)
        # convert dataframe to a list of records
        return enrollments.to_dict(orient='records')

    def construct_top_subjects_by_enrollments_csv(self, enrollments_df, start_date, end_date):
        """
        Construct top subjects by enrollments CSV.

        Arguments:
            enrollments_df {DataFrame} -- DataFrame of enrollments
            start_date {datetime} -- Enrollment start date in the format 'YYYY-MM-DD'
            end_date {datetime} -- Enrollment end date in the format 'YYYY-MM-DD'
        """
        enrollments = self.top_subjects_by_enrollments_common(enrollments_df, start_date, end_date)
        enrollments = enrollments.pivot(index="course_subject", columns="enroll_type", values="count")

        filename = f"Top 10 Subjects by Enrollment, {start_date} - {end_date}.csv"
        return self.construct_csv_response(enrollments, filename)

    def construct_csv_response(self, enrollments, filename):
        """
        Construct CSV response.

        Arguments:
            enrollments {DataFrame} -- DataFrame of enrollments
            filename {str} -- Filename for the CSV
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        enrollments.to_csv(path_or_buf=response)

        return response
