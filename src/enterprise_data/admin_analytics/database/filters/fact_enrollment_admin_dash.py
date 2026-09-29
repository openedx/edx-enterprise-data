"""
Query filters for enrollments table.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.filters.mixins import CommonFiltersMixin


class FactEnrollmentAdminDashFilters(CommonFiltersMixin, BaseFilter):
    """
    Query filters for enrollments table.
    """
