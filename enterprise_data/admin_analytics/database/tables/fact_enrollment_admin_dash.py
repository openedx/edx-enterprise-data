"""
Module for interacting with the fact_enrollment_admin_dash table.
"""
from datetime import date, datetime
from uuid import UUID

from enterprise_data.cache.decorators import cache_it

from ..queries import FactEnrollmentAdminDashQueries
from ..utils import run_query
from .base import BaseTable


class FactEnrollmentAdminDashTable(BaseTable):
    """
    Class for communicating with the fact_enrollment_admin_dash table.
    """
    queries = FactEnrollmentAdminDashQueries()

    def get_top_enterprises(self, count=10):
        """
        Get the top enterprises by enrollments.

        Arguments:
            count (int): The number of enterprises to return.

        Returns:
            list<str>: A list of enterprise UUIDs.
        """
        result = run_query(
            query=self.queries.get_top_enterprises_query(count),
            as_dict=False,
        )
        return [row[0] for row in result]

    @cache_it()
    def get_enrollment_count(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the total number of enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            (int): The total number of enrollments.
        """
        results = run_query(
            query=self.queries.get_enrollment_count_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        if not results:
            return 0
        return int(results[0][0] or 0)

    @cache_it()
    def get_all_enrollments(
            self, enterprise_customer_uuid: UUID, start_date: date, end_date: date, limit: int, offset: int
    ):
        """
        Get all enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            list<dict>: A list of dictionaries containing the enrollment data.
        """
        return run_query(
            query=self.queries.get_all_enrollments_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
                'offset': offset,
            },
            as_dict=True,
        )

    @cache_it()
    def get_enrollment_date_range(self, enterprise_customer_uuid: UUID):
        """
        Get the enrollment date range for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID | str): The UUID of the enterprise customer.

        Returns:
            (tuple<date, date>): The minimum and maximum enrollment dates.
        """
        results = run_query(
            query=self.queries.get_enrollment_date_range_query(),
            params={'enterprise_customer_uuid': enterprise_customer_uuid}
        )
        if not results:
            return None, None
        min_date, max_date = results[0]

        # We should return date objects, not datetime objects
        # This is done to counter cases where database values are datetime objects.
        if min_date and isinstance(min_date, datetime):
            min_date = min_date.date()
        if max_date and isinstance(max_date, datetime):
            max_date = max_date.date()

        return min_date, max_date

    @cache_it()
    def get_enrollment_and_course_count(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the enrollment and course count for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            (tuple<int, int>): The enrollment and course count.
        """
        results = run_query(
            query=self.queries.get_enrollment_and_course_count_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        if not results:
            return 0, 0
        return tuple(results[0])

    @cache_it()
    def get_completion_count(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the completion count for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            int: The completion count.
        """
        results = run_query(
            query=self.queries.get_completion_count_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        if not results:
            return 0

        return int(results[0][0] or 0)

    @cache_it()
    def get_top_courses_by_enrollments(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top courses enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the course key, course_title and enrollment count.
        """
        return run_query(
            query=self.queries.get_top_courses_by_enrollments_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_enrollments(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top subjects by enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the subject and enrollment count.
        """
        return run_query(
            query=self.queries.get_top_subjects_by_enrollments_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_enrolment_time_series_data(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the enrollment time series data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the date and enrollment count.
        """
        return run_query(
            query=self.queries.get_enrolment_time_series_data_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_all_completions(
            self, enterprise_customer_uuid: UUID, start_date: date, end_date: date, limit: int, offset: int
    ):
        """
        Get all completions for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            list<dict>: A list of dictionaries containing the completions data.
        """
        return run_query(
            query=self.queries.get_all_completions_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
                'offset': offset,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_courses_by_completions(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top courses by completion for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the course key, course_title and completion count.
        """
        return run_query(
            query=self.queries.get_top_courses_by_completions_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_completions(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top subjects by completions for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the subject and completion count.
        """
        return run_query(
            query=self.queries.get_top_subjects_by_completions_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_completions_time_series_data(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the completions time series data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the date and completion count.
        """
        return run_query(
            query=self.queries.get_completions_time_series_data_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )
