"""
Views for fetching leaderboard data.
"""

from datetime import date
from logging import getLogger

from edx_rbac.decorators import permission_required
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.viewsets import ViewSet

from django.http import StreamingHttpResponse

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.admin_analytics.database.tables import FactEngagementAdminDashTable, FactEnrollmentAdminDashTable
from enterprise_data.api.v1.serializers import AdvanceAnalyticsQueryParamSerializer
from enterprise_data.api.v1.views.base import AnalyticsPaginationMixin
from enterprise_data.renderers import LeaderboardCSVRenderer

LOGGER = getLogger(__name__)


class AdvanceAnalyticsLeaderboardView(AnalyticsPaginationMixin, ViewSet):
    """
    View to handle requests for enterprise leaderboard data.

    Here is the list of URLs that are handled by this view:
    1. `enterprise_data_api_v1.enterprise-admin-analytics-leaderboard-list`: Get leaderboard data.
    """
    authentication_classes = (JwtAuthentication,)
    http_method_names = ('get', )

    @permission_required('can_access_enterprise', fn=lambda request, enterprise_uuid: enterprise_uuid)
    def list(self, request, enterprise_uuid):
        """
        Get individual leaderboard data for the enterprise.
        """
        # Remove hyphens from the UUID
        enterprise_uuid = enterprise_uuid.replace('-', '')

        serializer = AdvanceAnalyticsQueryParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        min_enrollment_date, _ = FactEnrollmentAdminDashTable().get_enrollment_date_range(
            enterprise_uuid,
        )

        # get values from query params or use default values
        start_date = serializer.data.get('start_date', min_enrollment_date)
        end_date = serializer.data.get('end_date', date.today())
        page = serializer.data.get('page', 1)
        page_size = serializer.data.get('page_size', 100)
        total_count = FactEngagementAdminDashTable().get_leaderboard_data_count(
            enterprise_customer_uuid=enterprise_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        leaderboard = FactEngagementAdminDashTable().get_all_leaderboard_data(
            enterprise_customer_uuid=enterprise_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=(page - 1) * page_size,
            total_count=total_count,
        )
        response_type = request.query_params.get('response_type', ResponseType.JSON.value)

        LOGGER.info(
            'Leaderboard data requested for enterprise [%s] from [%s] to [%s]',
            enterprise_uuid,
            start_date,
            end_date,
        )

        if response_type == ResponseType.CSV.value:
            filename = f'Leaderboard, {start_date} - {end_date}.csv'

            return StreamingHttpResponse(
                LeaderboardCSVRenderer().render(self._stream_serialized_data(
                    enterprise_uuid, start_date, end_date, total_count
                )),
                content_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'},
            )

        return self.get_paginated_response(
            request=request,
            records=leaderboard,
            page=page,
            page_size=page_size,
            total_count=total_count,
        )

    @staticmethod
    def _stream_serialized_data(enterprise_uuid, start_date, end_date, total_count, page_size=50000):
        """
        Stream the serialized data.
        """
        offset = 0
        while offset < total_count:
            leaderboard = FactEngagementAdminDashTable().get_all_leaderboard_data(
                enterprise_customer_uuid=enterprise_uuid,
                start_date=start_date,
                end_date=end_date,
                limit=page_size,
                offset=offset,
                total_count=total_count,
            )
            yield from leaderboard
            offset += page_size
