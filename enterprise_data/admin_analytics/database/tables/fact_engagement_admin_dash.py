"""
Module for interacting with the fact_enrollment_engagement_day_admin_dash table.
"""
from datetime import date
from uuid import UUID

from ..queries import FactEngagementAdminDashQueries
from ..utils import run_query
from .base import BaseTable


class FactEngagementAdminDashTable(BaseTable):
    """
    Class for communicating with the fact_enrollment_engagement_day_admin_dash table.
    """
    queries = FactEngagementAdminDashQueries()

    def get_learning_hours_and_daily_sessions(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the learning hours and daily sessions for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            (tuple<float, int>): The learning hours and daily sessions.
        """
        results = run_query(
            query=self.queries.get_learning_hours_and_daily_sessions_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        return tuple(results[0])
