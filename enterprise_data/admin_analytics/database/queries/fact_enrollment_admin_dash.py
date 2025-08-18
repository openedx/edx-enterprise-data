"""
Module containing queries for the fact_enrollment_admin_dash table.
"""
from ..query_filters import QueryFilters


class FactEnrollmentAdminDashQueries:
    """
    Queries related to the fact_enrollment_admin_dash table.
    """
    @staticmethod
    def get_top_enterprises_query(count=10):
        """
        Get the query to fetch the top enterprises by enrollments.
        """
        return f"""
            SELECT enterprise_customer_uuid
            FROM fact_enrollment_admin_dash
            GROUP BY enterprise_customer_uuid
            ORDER BY COUNT(enterprise_customer_uuid) DESC LIMIT {count};
        """

    @staticmethod
    def get_enrollment_count_query(query_filters: QueryFilters) -> str:
        """
        Get the query to fetch the total number of enrollments for an enterprise customer.
        """
        return f"""
            SELECT count(*)
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()};
        """

    @staticmethod
    def get_all_enrollments_query(query_filters: QueryFilters) -> str:
        """
        Get the query to fetch all enrollments.
        """
        return f"""
            SELECT email, course_title, course_subject, enroll_type, enterprise_enrollment_date
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()}
            ORDER BY ENTERPRISE_ENROLLMENT_DATE DESC LIMIT %(limit)s OFFSET %(offset)s
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
    def get_completion_count_query(query_filters: QueryFilters) -> str:
        """
        Get the query to fetch the completion count.
        """
        return f"""
            SELECT
                SUM(has_passed) as completions
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()};
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

    @staticmethod
    def get_top_courses_by_enrollments_query(query_filters: QueryFilters, record_count: int = 10) -> str:
        """
        Get the query to fetch the enrollment count by courses.

        Query will fetch the top N courses by enrollment count. Where N is the value of record_count.

        Arguments:
            query_filters (QueryFilters): List of query filters.
            record_count (int): Number of records to fetch.
        """
        return f"""
            WITH filtered_data AS (
                SELECT *
                FROM fact_enrollment_admin_dash
                WHERE {query_filters.to_sql()}
            ),
            top_10_courses AS (
                SELECT course_key
                FROM filtered_data
                GROUP BY course_key
                ORDER BY COUNT(*) DESC
                LIMIT {record_count}
            )

            SELECT
                d.course_key,
                MAX(d.course_title) AS course_title,
                d.enroll_type,
                COUNT(*) AS enrollment_count
            FROM filtered_data d
            JOIN top_10_courses tc
                ON d.course_key = tc.course_key
            GROUP BY d.course_key, d.enroll_type;
        """

    @staticmethod
    def get_top_subjects_by_enrollments_query(query_filters: QueryFilters, record_count: int = 10) -> str:
        """
        Get the query to fetch the enrollment count by subjects.

        Query will fetch the top N subjects by enrollment count. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.
            query_filters (QueryFilters): List of query filters.
        """
        return f"""
            WITH filtered_data AS (
                SELECT *
                FROM fact_enrollment_admin_dash
                WHERE {query_filters.to_sql()}
            ),
            top_10_subjects AS (
                SELECT course_subject
                FROM filtered_data
                GROUP BY course_subject
                ORDER BY COUNT(*) DESC
                LIMIT {record_count}
            )
            SELECT
                d.course_subject,
                d.enroll_type,
                COUNT(*) AS enrollment_count
            FROM filtered_data d
            JOIN top_10_subjects ts
                ON d.course_subject = ts.course_subject
            GROUP BY d.course_subject, d.enroll_type;
        """

    @staticmethod
    def get_enrolment_time_series_data_query(query_filters: QueryFilters) -> str:
        """
        Get the query to fetch the enrollment time series data with daily aggregation.

        Arguments:
            query_filters (QueryFilters): A list of filters for this query.
        """
        return f"""
            SELECT enterprise_enrollment_date, enroll_type, COUNT(*) as enrollment_count
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()}
            GROUP BY enterprise_enrollment_date, enroll_type
            ORDER BY enterprise_enrollment_date;
        """

    @staticmethod
    def get_all_completions_query(
        query_filters: QueryFilters,
    ) -> str:
        """
        Get the query to fetch all completions.
        """
        return f"""
            SELECT email, course_title, course_subject, enroll_type, passed_date
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()}
            ORDER BY passed_date DESC LIMIT %(limit)s OFFSET %(offset)s
        """

    @staticmethod
    def get_top_courses_by_completions_query(query_filters: QueryFilters, record_count=10) -> str:
        """
        Get the query to fetch the completion count by courses.

        Query should fetch the top N courses by completion count. Where N is the value of record_count.

        Arguments:
            query_filters (QueryFilters): List of query filters.
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the enrollment count by courses for the top courses by enrollment count.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    course_key,
                    course_title,
                    enroll_type,
                    passed_date
                FROM fact_enrollment_admin_dash
                WHERE {query_filters.to_sql()}
            ),
            top_10_courses AS (
                SELECT
                    course_key,
                    COUNT(*) AS total_completion_count
                FROM filtered_data
                GROUP BY course_key
                ORDER BY total_completion_count DESC
                LIMIT {record_count}
            )
            SELECT
                d.course_key,
                d.course_title,
                d.enroll_type,
                COUNT(*) AS completion_count
            FROM filtered_data d
            JOIN top_10_courses tc
                ON d.course_key = tc.course_key
            GROUP BY d.course_key, d.course_title, d.enroll_type
            ORDER BY total_completion_count DESC;
        """

    @staticmethod
    def get_top_subjects_by_completions_query(query_filters: QueryFilters, record_count=10) -> str:
        """
        Get the query to fetch the completion count by subjects.

        Query should fetch the top N subjects by completion count. Where N is the value of record_count.

        Arguments:
            query_filters (QueryFilters): List of query filters.
            record_count (int): Number of records to fetch.

        Returns:
            (str): Query to fetch the completion count by subjects for the top subjects by completion count.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    course_subject,
                    enroll_type,
                    passed_date
                FROM fact_enrollment_admin_dash
                WHERE {query_filters.to_sql()}
            ),
            top_10_subjects AS (
                SELECT
                    course_subject,
                    COUNT(*) AS total_completion_count
                FROM filtered_data
                GROUP BY course_subject
                ORDER BY total_completion_count DESC
                LIMIT {record_count}
            )
            SELECT
                d.course_subject,
                d.enroll_type,
                COUNT(*) AS completion_count
            FROM filtered_data d
            JOIN top_10_subjects ts
                ON d.course_subject = ts.course_subject
            GROUP BY d.course_subject, d.enroll_type
            ORDER BY total_completion_count DESC;
        """

    @staticmethod
    def get_completions_time_series_data_query(
        query_filters: QueryFilters,
    ) -> str:
        """
        Get the query to fetch the completion time series data.

        Query should fetch the time series data with daily granularity.

        Returns:
            (str): Query to fetch the completion time series data.
        """
        return f"""
            SELECT passed_date, enroll_type, count(course_key) as completion_count
            FROM fact_enrollment_admin_dash
            WHERE {query_filters.to_sql()}
            GROUP BY passed_date, enroll_type
            ORDER BY passed_date;
        """

    @staticmethod
    def get_enrolled_courses(
        query_filters: QueryFilters
    ) -> str:
        """
        Get the query to fetch the enrolled courses.

        Returns:
            (str): Query to fetch the enrolled courses.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    DISTINCT course_key, course_title
                FROM
                    fact_enrollment_admin_dash
                WHERE {query_filters.to_sql()}
            )
            SELECT
                course_key,
                course_title
            FROM
                filtered_data
        """
