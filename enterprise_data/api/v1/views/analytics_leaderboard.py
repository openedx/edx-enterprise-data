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
from enterprise_data.admin_analytics.database.tables import FactEngagementAdminDashTable, FactEnrollmentAdminDashTable
from enterprise_data.api.v1.paginators import AdvanceAnalyticsPagination
from enterprise_data.api.v1.serializers import AdvanceAnalyticsQueryParamSerializer
from enterprise_data.renderers import LeaderboardCSVRenderer

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
        enterprise_uuid = enterprise_uuid.replace('-', '')
        serializer = AdvanceAnalyticsQueryParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        if (start_date := serializer.data.get('start_date')) is None:
            start_date, _ = FactEnrollmentAdminDashTable().get_enrollment_date_range(enterprise_uuid)

        end_date = serializer.data.get('end_date', datetime.now())
        response_type = request.query_params.get('response_type', ResponseType.JSON.value)
        leaderboard = FactEngagementAdminDashTable().get_leaderboard(enterprise_uuid, start_date, end_date)
        leaderboard_df = pd.DataFrame(leaderboard)
        # move the aggregated row with email 'null' to the end of the table
        idx = leaderboard_df.index[leaderboard_df['email'] == 'null']
        leaderboard_df.loc[idx, 'email'] = 'learners who have not shared consent'
        leaderboard_df = pd.concat([leaderboard_df.drop(idx), leaderboard_df.loc[idx]])

        # convert `nan` values to `None` because `nan` is not JSON serializable
        leaderboard_df = leaderboard_df.replace(np.nan, None)

        if response_type == ResponseType.CSV.value:
            filename = f"""Leaderboard, {start_date} - {end_date}.csv"""
            leaderboard_df = leaderboard_df[
                [
                    "email",
                    "learning_time_hours",
                    "sessions",
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
