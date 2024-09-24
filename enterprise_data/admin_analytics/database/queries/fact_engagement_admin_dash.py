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

    @staticmethod
    def get_engagement_count_query():
        """
        Get the query to fetch the total number of engagements for an enterprise customer.
        """
        return """
            SELECT count(*)
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s;
        """

    @staticmethod
    def get_all_engagement_query():
        """
        Get the query to fetch all engagement data.
        """
        return """
            SELECT
                email, course_title, course_subject, enroll_type, activity_date,
                learning_time_seconds/3600 as learning_time_hours
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY activity_date DESC LIMIT %(limit)s OFFSET %(offset)s;
        """

    @staticmethod
    def get_top_courses_by_engagement_query(record_count=20):
        """
        Get the query to fetch the learning time in hours by courses.

        Query should fetch the top N courses by user engagement. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the learning time in hours by courses for the top courses by user engagement.
        """
        return f"""
            SELECT course_key, course_title, enroll_type, SUM(learning_time_seconds)/3600 as learning_time_hours
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY course_key, course_title, enroll_type
            ORDER BY learning_time_hours DESC LIMIT {record_count};
        """

    @staticmethod
    def get_top_subjects_by_engagement_query(record_count=20):
        """
        Get the query to fetch the learning time in hours by subjects.

        Query should fetch the top N subjects by user engagement. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the learning time in hours by subjects for the top subjects by user engagement.
        """
        return f"""
            SELECT course_subject, enroll_type, SUM(learning_time_seconds)/3600 as learning_time_hours
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY course_subject, enroll_type
            ORDER BY learning_time_hours DESC LIMIT {record_count};
        """

    @staticmethod
    def get_engagement_time_series_data_query():
        """
        Get the query to fetch the completion time series data.

        Query should fetch the time series data with daily granularity.

        Returns:
            (str): Query to fetch the completion time series data.
        """
        return """
            SELECT activity_date, enroll_type, SUM(learning_time_seconds)/3600 as learning_time_hours
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY activity_date, enroll_type
            ORDER BY activity_date;
        """