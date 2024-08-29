"""
Module containing queries for the fact_enrollment_admin_dash table.
"""


class FactEnrollmentAdminDashQueries:
    """
    Queries related to the fact_enrollment_admin_dash table.
    """

    @staticmethod
    def get_enrollment_date_range_query():
        """
        Get the query to fetch the enrollment date range.
        """
        return """
            SELECT
                MIN(enterprise_enrollment_date) AS min_enrollment_date,
                MAX(enterprise_enrollment_date) AS max_enrollment_date
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s;
        """

    @staticmethod
    def get_enrollment_and_course_count_query():
        """
        Get the query to fetch the enrollment and course count.
        """
        return """
            SELECT
                count(*) as enrolls, count(DISTINCT course_key) as courses
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s;
        """

    @staticmethod
    def get_completion_count_query():
        """
        Get the query to fetch the completion count.
        """
        return """
            SELECT
                SUM(has_passed) as completions
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                passed_date BETWEEN %(start_date)s AND %(end_date)s;
        """

    @staticmethod
    def get_learning_hours_and_daily_sessions_query():
        """
        Get the query to fetch the learning hours and daily sessions.
        """
        return """
            SELECT
                ROUND(SUM(learning_time_seconds) / 60 / 60, 1) as hours, SUM(is_engaged) as sessions
            FROM fact_engagement_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s;
        """
