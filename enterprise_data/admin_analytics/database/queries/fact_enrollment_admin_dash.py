"""
Module containing queries for the fact_enrollment_admin_dash table.
"""


class FactEnrollmentAdminDashQueries:
    """
    Queries related to the fact_enrollment_admin_dash table.
    """
    @staticmethod
    def get_enrollment_count_query():
        """
        Get the query to fetch the total number of enrollments for an enterprise customer.
        """
        return """
            SELECT count(*)
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s;
        """

    @staticmethod
    def get_all_enrollments_query():
        """
        Get the query to fetch all enrollments.
        """
        return """
            SELECT email, course_title, course_subject, enroll_type, enterprise_enrollment_date
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s
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

    @staticmethod
    def get_top_courses_enrollments_query(record_count=20):
        """
        Get the query to fetch the enrollment count by courses.

        Query will fetch the top N courses by enrollment count. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.
        """
        # Some local environments raise error when course_title is added in SELECT without GROUP BY.
        # If you face this issue, you can remove course_title from SELECT.
        return f"""
            SELECT course_key, course_title , enroll_type, count(course_key) as enrollment_count
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY course_key, enroll_type ORDER BY enrollment_count DESC LIMIT {record_count};
        """

    @staticmethod
    def get_top_subjects_by_enrollments_query(record_count=20):
        """
        Get the query to fetch the enrollment count by subjects.

        Query will fetch the top N subjects by enrollment count. Where N is the value of record_count.

        Arguments:
            record_count (int): Number of records to fetch.
        """
        return f"""
            SELECT course_subject, enroll_type, count(course_subject) enrollment_count
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY course_subject, enroll_type ORDER BY enrollment_count DESC LIMIT {record_count};
        """

    @staticmethod
    def get_enrolment_time_series_data_query():
        """
        Get the query to fetch the enrollment time series data with daily aggregation.
        """
        return """
            SELECT enterprise_enrollment_date, enroll_type, COUNT(*) as enrollment_count
            FROM fact_enrollment_admin_dash
            WHERE enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                enterprise_enrollment_date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY enterprise_enrollment_date, enroll_type
            ORDER BY enterprise_enrollment_date;
        """
