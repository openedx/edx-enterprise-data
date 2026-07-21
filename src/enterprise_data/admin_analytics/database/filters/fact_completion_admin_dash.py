"""
Query filters for enrollments table.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.filters.mixins import CommonFiltersMixin
from enterprise_data.admin_analytics.database.query_filters import EqualQueryFilter


class FactCompletionAdminDashFilters(CommonFiltersMixin, BaseFilter):
    """
    Query filters for completions data in enrollments table.
    """

    @staticmethod
    def has_passed_filter() -> EqualQueryFilter:
        """
        Filter by has passed with fixed value 1.
        """
        return EqualQueryFilter(
            column='has_passed',
            value=1
        )
