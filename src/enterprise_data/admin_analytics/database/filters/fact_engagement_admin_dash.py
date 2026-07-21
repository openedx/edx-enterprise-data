"""
Query filters for engagments data.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.filters.mixins import CommonFiltersMixin


class FactEngagementAdminDashFilters(CommonFiltersMixin, BaseFilter):
    """
    Query filters for engagments data.
    """
