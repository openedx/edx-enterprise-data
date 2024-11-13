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
    def get_top_courses_by_engagement_query(record_count=10):
        """
        Get the query to fetch the learning time in hours by courses.

        Query should fetch the top N courses by user engagement. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the learning time in hours by courses for the top courses by user engagement.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    course_key,
                    course_title,
                    enroll_type,
                    (learning_time_seconds / 60.0 / 60.0) AS learning_time_hours,
                    activity_date
                FROM fact_enrollment_engagement_day_admin_dash
                WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            ),
            top_10_courses AS (
                SELECT
                    course_key,
                    SUM(learning_time_hours) as total_learning_time
                FROM filtered_data
                GROUP BY course_key
                ORDER BY total_learning_time DESC
                LIMIT {record_count}
            )
            SELECT
                d.course_key,
                d.course_title,
                d.enroll_type,
                ROUND(SUM(d.learning_time_hours)) AS learning_time_hours
            FROM filtered_data d
            JOIN top_10_courses tc
                ON d.course_key = tc.course_key
            GROUP BY d.course_key, d.course_title, d.enroll_type
            ORDER BY total_learning_time DESC;
        """

    @staticmethod
    def get_top_subjects_by_engagement_query(record_count=10):
        """
        Get the query to fetch the learning time in hours by subjects.

        Query should fetch the top N subjects by user engagement. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the learning time in hours by subjects for the top subjects by user engagement.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    course_subject,
                    enroll_type,
                    (learning_time_seconds / 60.0 / 60.0) AS learning_time_hours,
                    activity_date
                FROM fact_enrollment_engagement_day_admin_dash
                WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                activity_date BETWEEN %(start_date)s AND %(end_date)s
            ),
            top_10_subjects AS (
                SELECT
                    course_subject,
                    SUM(learning_time_hours) as total_learning_time
                FROM filtered_data
                GROUP BY course_subject
                ORDER BY total_learning_time DESC
                LIMIT {record_count}
            )
            SELECT
                d.course_subject,
                d.enroll_type,
                ROUND(SUM(d.learning_time_hours)) AS learning_time_hours
            FROM filtered_data d
            JOIN top_10_subjects ts
                ON d.course_subject = ts.course_subject
            GROUP BY d.course_subject, d.enroll_type
            ORDER BY total_learning_time DESC;
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

    @staticmethod
    def get_engagement_data_for_leaderboard_query():
        """
        Get the query to fetch the engagement data for leaderboard.

        Query should fetch the engagement data for like learning time, session length of
        the enterprise learners to show in the leaderboard.

        Returns:
            (str): Query to fetch the engagement data for leaderboard.
        """
        return """
            SELECT
                email,
                ROUND(SUM(learning_time_seconds) / 3600, 1) as learning_time_hours,
                SUM(is_engaged) as session_count,
                CASE
                    WHEN SUM(is_engaged) = 0 THEN 0.0
                    ELSE ROUND(SUM(learning_time_seconds) / 3600 / SUM(is_engaged), 1)
                END AS average_session_length
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                (activity_date BETWEEN %(start_date)s AND %(end_date)s) AND
                is_engaged = 1
            GROUP BY email
            ORDER BY learning_time_hours DESC
            LIMIT %(limit)s OFFSET %(offset)s;
        """

    @staticmethod
    def get_completion_data_for_leaderboard_query(email_list: list):
        """
        Get the query to fetch the completions data for leaderboard.

        Query should fetch the completion data for like course completion count of
        the enterprise learners to show in the leaderboard.

        Arguments:
            email_list (str): List of emails to filter the completions data.

        Returns:
            (list<str>): Query to fetch the completions data for leaderboard.
        """
        return f"""
            SELECT email, count(course_key) as course_completion_count
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                (passed_date BETWEEN %(start_date)s AND %(end_date)s) AND
                has_passed = 1 AND
                email IN {str(tuple(email_list))}
            GROUP BY email;
        """

    @staticmethod
    def get_engagement_data_for_leaderboard_null_email_only_query():
        """
        Get the query to fetch the engagement data for leaderboard for NULL emails only.

        Query should fetch the engagement data for like learning time, session length of
        the enterprise learners to show in the leaderboard.

        Returns:
            (str): Query to fetch the engagement data for leaderboard.
        """
        return """
            SELECT
                email,
                ROUND(SUM(learning_time_seconds) / 3600, 1) as learning_time_hours,
                SUM(is_engaged) as session_count,
                CASE
                    WHEN SUM(is_engaged) = 0 THEN 0.0
                    ELSE ROUND(SUM(learning_time_seconds) / 3600 / SUM(is_engaged), 1)
                END AS average_session_length
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                (activity_date BETWEEN %(start_date)s AND %(end_date)s) AND
                is_engaged = 1 AND
                email is NULL
            GROUP BY email;
        """

    @staticmethod
    def get_completion_data_for_leaderboard_null_email_only_query():
        """
        Get the query to fetch the completions data for leaderboard for NULL emails.

        Query should fetch the completion data for like course completion count of
        the enterprise learners to show in the leaderboard.

        Returns:
            (list<str>): Query to fetch the completions data for leaderboard.
        """
        return """
            SELECT email, count(course_key) as course_completion_count
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                (passed_date BETWEEN %(start_date)s AND %(end_date)s) AND
                has_passed = 1 AND
                email is NULL
            GROUP BY email;
        """

    @staticmethod
    def get_leaderboard_data_count_query():
        """
        Get the query to fetch the leaderboard row count and null email counter.

        Query should fetch the count of rows for the leaderboard data for the enterprise customer.

        Returns:
            (str): Query to fetch the leaderboard row count.
        """
        return """
            SELECT
                COUNT(*) OVER () AS record_count
            FROM fact_enrollment_engagement_day_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                (activity_date BETWEEN %(start_date)s AND %(end_date)s) AND
                is_engaged = 1
            GROUP BY email
            LIMIT 1;
        """
