"""Advance Analytics for Enrollments"""
from datetime import datetime

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import HttpResponse, StreamingHttpResponse

from enterprise_data.admin_analytics.constants import CALCULATION, ENROLLMENT_CSV, GRANULARITY
from enterprise_data.admin_analytics.utils import (
    calculation_aggregation,
    fetch_and_cache_enrollments_data,
    fetch_enrollments_cache_expiry_timestamp,
    granularity_aggregation,
)
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.api.v1.serializers import (
    AdvanceAnalyticsEnrollmentSerializer,
    AdvanceAnalyticsEnrollmentStatsSerializer,
)
from enterprise_data.renderers import IndividualEnrollmentsCSVRenderer
from enterprise_data.utils import date_filter


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

        if csv_type == ENROLLMENT_CSV.INDIVIDUAL_ENROLLMENTS.value:
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
    def get(self, request, enterprise_uuid):  # lint-amnesty, pylint: disable=inconsistent-return-statements
        """Get enrollment chart stats"""
        serializer = AdvanceAnalyticsEnrollmentStatsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, cache_expiry)

        # get values from query params or use default
        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        granularity = serializer.data.get('granularity', GRANULARITY.DAILY.value)
        calculation = serializer.data.get('calculation', CALCULATION.TOTAL.value)
        csv_type = serializer.data.get('csv_type')

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
            return Response(data)
        elif csv_type == ENROLLMENT_CSV.ENROLLMENTS_OVER_TIME.value:
            return self.construct_enrollments_over_time_csv(
                enrollments_df.copy(),
                start_date,
                end_date,
                granularity,
                calculation,
            )
        elif csv_type == ENROLLMENT_CSV.TOP_COURSES_BY_ENROLLMENTS.value:
            return self.construct_top_courses_by_enrollments_csv(
                enrollments_df.copy(),
                start_date,
                end_date,
            )
        elif csv_type == ENROLLMENT_CSV.TOP_SUBJECTS_BY_ENROLLMENTS.value:
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
            granularity {str} -- Granularity of the data. One of GRANULARITY choices
            calculation {str} -- Calculation of the data. One of CALCULATION choices
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
            granularity {str} -- Granularity of the data. One of GRANULARITY choices
            calculation {str} -- Calculation of the data. One of CALCULATION choices
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
            granularity {str} -- Granularity of the data. One of GRANULARITY choices
            calculation {str} -- Calculation of the data. One of CALCULATION choices
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
        enrollments.to_csv(path_or_buf=response)

        return response