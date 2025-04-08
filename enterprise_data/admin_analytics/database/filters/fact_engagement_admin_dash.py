"""
Query filters for engagements table.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.query_filters import BetweenQueryFilter


class FactEngagementAdminDashFilters(BaseFilter):
    """
    Query filters for engagements table.
    """
    @staticmethod
    def enterprise_date_range_filter(
            start_date_params_key: str, end_date_params_key: str
    ) -> BetweenQueryFilter:
        """
        Filter by enrollment date to be in the given range.

        Arguments:
            start_date_params_key (str): The start date key against which value will be passed in the query.
            end_date_params_key (str): The end date key against which value will be passed in the query.
        """
        return BetweenQueryFilter(
            column='activity_date',
            range_placeholders=(start_date_params_key, end_date_params_key),
        )
