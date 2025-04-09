"""
Query filters for enrollments table.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.query_filters import BetweenQueryFilter, EqualQueryFilter


class FactCompletionAdminDashFilters(BaseFilter):
    """
    Query filters for completions data in enrollments table.
    """
    @staticmethod
    def passed_date_range_filter(
            start_date_params_key: str, end_date_params_key: str
    ) -> BetweenQueryFilter:
        """
        Filter by passed date to be in the given range.

        Arguments:
            start_date_params_key (str): The start date key against which value will be passed in the query.
            end_date_params_key (str): The end date key against which value will be passed in the query.
        """
        return BetweenQueryFilter(
            column='passed_date',
            range_placeholders=(start_date_params_key, end_date_params_key),
        )

    @staticmethod
    def has_passed_filter() -> EqualQueryFilter:
        """
        Filter by has passed with fixed value 1.
        """
        return EqualQueryFilter(
            column='has_passed',
            value=1
        )
