"""Advance Analytics for Leaderboard"""
from datetime import datetime
from logging import getLogger

import numpy as np
import pandas as pd
from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.views import APIView

from django.http import StreamingHttpResponse

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.admin_analytics.utils import (
    fetch_and_cache_engagements_data,
    fetch_and_cache_enrollments_data,
    fetch_engagements_cache_expiry_timestamp,
    fetch_enrollments_cache_expiry_timestamp,
)
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.api.v1.serializers import AdvanceAnalyticsQueryParamSerializer
from enterprise_data.renderers import LeaderboardCSVRenderer
from enterprise_data.utils import date_filter

LOGGER = getLogger(__name__)


class AdvanceAnalyticsLeaderboardView(APIView):
    """
    API for getting the advance analytics leaderboard data.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = AdvanceAnalyticsPagination
    http_method_names = ['get']

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def get(self, request, enterprise_uuid):
        """Get leaderboard data"""
        serializer = AdvanceAnalyticsQueryParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        enrollments_cache_expiry = fetch_enrollments_cache_expiry_timestamp()
        enrollments_df = fetch_and_cache_enrollments_data(enterprise_uuid, enrollments_cache_expiry)

        engagements_cache_expiry = fetch_engagements_cache_expiry_timestamp()
        engagements_df = fetch_and_cache_engagements_data(enterprise_uuid, engagements_cache_expiry)

        start_date = serializer.data.get('start_date', enrollments_df.enterprise_enrollment_date.min())
        end_date = serializer.data.get('end_date', datetime.now())
        response_type = serializer.data.get('response_type', ResponseType.JSON.value)

        LOGGER.info(
            "Leaderboard data requested for enterprise [%s] from [%s] to [%s]",
            enterprise_uuid,
            start_date,
            end_date,
        )

        # only include learners who have passed the course
        enrollments_df = enrollments_df[enrollments_df["has_passed"] == 1]

        # filter enrollments by date
        enrollments_df = date_filter(start_date, end_date, enrollments_df, "passed_date")

        completions = enrollments_df.groupby(["email"]).size().reset_index()
        completions.columns = ["email", "course_completions"]

        # filter engagements by date
        engagements_df = date_filter(start_date, end_date, engagements_df, "activity_date")

        engage = (
            engagements_df.groupby(["email"])
            .agg({"is_engaged": ["sum"], "learning_time_seconds": ["sum"]})
            .reset_index()
        )
        engage.columns = ["email", "daily_sessions", "learning_time_seconds"]
        engage["learning_time_hours"] = round(
            engage["learning_time_seconds"].astype("float") / 60 / 60, 1
        )

        # if daily_sessions is 0, set average_session_length to 0 becuase otherwise it will be `inf`
        engage["average_session_length"] = np.where(
            engage["daily_sessions"] == 0,
            0,
            round(engage["learning_time_hours"] / engage["daily_sessions"].astype("float"), 1)
        )

        leaderboard_df = engage.merge(completions, on="email", how="left")
        leaderboard_df = leaderboard_df.sort_values(
            by=["learning_time_hours", "daily_sessions", "course_completions"],
            ascending=[False, False, False],
        )

        # move the aggregated row with email 'null' to the end of the table
        idx = leaderboard_df.index[leaderboard_df['email'] == 'null']
        leaderboard_df.loc[idx, 'email'] = 'learners who have not shared consent'
        leaderboard_df = pd.concat([leaderboard_df.drop(idx), leaderboard_df.loc[idx]])

        # convert `nan` values to `None` because `nan` is not JSON serializable
        leaderboard_df = leaderboard_df.replace(np.nan, None)

        LOGGER.info(
            "Leaderboard data prepared for enterprise [%s] from [%s] to [%s]",
            enterprise_uuid,
            start_date,
            end_date,
        )

        if response_type == ResponseType.CSV.value:
            filename = f"""Leaderboard, {start_date} - {end_date}.csv"""
            leaderboard_df = leaderboard_df[
                [
                    "email",
                    "learning_time_hours",
                    "daily_sessions",
                    "average_session_length",
                    "course_completions",
                ]
            ]
            return StreamingHttpResponse(
                LeaderboardCSVRenderer().render(self._stream_serialized_data(leaderboard_df)),
                content_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Access-Control-Expose-Headers": "Content-Disposition"
                },
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(leaderboard_df, request)
        serialized_data = page.data.to_dict(orient='records')
        response = paginator.get_paginated_response(serialized_data)

        return response

    def _stream_serialized_data(self, leaderboard_df, chunk_size=50000):
        """
        Stream the serialized data.
        """
        total_rows = leaderboard_df.shape[0]
        for start_index in range(0, total_rows, chunk_size):
            end_index = min(start_index + chunk_size, total_rows)
            chunk = leaderboard_df.iloc[start_index:end_index]
            yield from chunk.to_dict(orient='records')
