"""
Module containing queries for the fact_enrollment_engagement_day_admin_dash table.
"""


class FactEngagementAdminDashQueries:
    """
    Queries related to the fact_enrollment_engagement_day_admin_dash table.
    """
    @staticmethod
    def get_learning_hours_and_daily_sessions_query():
        """
        Get the query to fetch the learning hours and daily sessions.
        """
        return """
            SELECT
                ROUND(SUM(learning_time_seconds) / 60 / 60, 1) as hours, SUM(is_engaged) as sessions
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s;
        """
