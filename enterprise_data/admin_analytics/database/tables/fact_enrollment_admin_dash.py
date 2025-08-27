"""
Module for interacting with the fact_enrollment_admin_dash table.
"""
from datetime import date, datetime
from typing import Optional, Tuple
from uuid import UUID

from enterprise_data.admin_analytics.database.query_filters import EqualQueryFilter
from enterprise_data.cache.decorators import cache_it

from ..filters import FactCompletionAdminDashFilters, FactEnrollmentAdminDashFilters
from ..queries import FactEnrollmentAdminDashQueries
from ..query_filters import QueryFilters
from ..utils import run_query
from .base import BaseTable


class FactEnrollmentAdminDashTable(BaseTable):
    """
    Class for communicating with the fact_enrollment_admin_dash table.
    """
    queries = FactEnrollmentAdminDashQueries()
    enrollment_filters = FactEnrollmentAdminDashFilters()
    completion_filters = FactCompletionAdminDashFilters()

    def __get_common_query_filters(
            self, enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ) -> (QueryFilters, dict):
        """
        Utility method to get query filters common in most usages below.

        This will return a tuple containing the query filters list and the dictionary of query parameters that
        will be used in the query.

        It will contain the following query filters.
            1. enterprise_customer_uuid filter to filter records for an enterprise customer.
            2. enrollment_date range filter to filter records by enrollment date.
            3. group_uuid filter to filter records for learners who belong to the given group.
        """
        query_filters = QueryFilters([
            self.enrollment_filters.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
            self.enrollment_filters.date_range_filter('enterprise_enrollment_date', 'start_date', 'end_date'),
        ])
        params = {
            'enterprise_customer_uuid': enterprise_customer_uuid,
            'start_date': start_date,
            'end_date': end_date,
        }

        response = self.enrollment_filters.enterprise_user_query_filter(
            group_uuid, enterprise_customer_uuid
        )
        if response is not None:
            enterprise_user_id_in_filter, enterprise_user_id_params = response
            query_filters.append(enterprise_user_id_in_filter)
            params.update(enterprise_user_id_params)

        # add optional filters
        if course_type:
            query_filters.append(EqualQueryFilter(
                column='course_product_line',
                value_placeholder='course_type',
            ))
            params['course_type'] = course_type

        if course_key:
            query_filters.append(EqualQueryFilter(
                column='course_key',
                value_placeholder='course_key',
            ))
            params['course_key'] = course_key

        if budget_uuid:
            query_filters.append(EqualQueryFilter(
                column='subsidy_access_policy_uuid',
                value_placeholder='budget_uuid',
            ))
            params['budget_uuid'] = budget_uuid

        return query_filters, params

    def __get_common_query_filters_for_completion(
        self, enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ) -> Tuple[QueryFilters, dict]:
        """
        Utility method to get query filters common in most usages below.

        This will return a tuple containing the query filters list and the dictionary of query parameters that
        will be used in the query.

        It will contain the following query filters.
            1. enterprise_customer_uuid filter to filter records for an enterprise customer.
            2. enrollment_date range filter to filter records by enrollment date.
            3. group_uuid filter to filter records for learners who belong to the given group.
            4. has_passed filter to filter records for successful completions.
        """
        query_filters = QueryFilters([
            self.completion_filters.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
            self.completion_filters.date_range_filter('passed_date', 'start_date', 'end_date'),
            self.completion_filters.has_passed_filter(),
        ])
        params = {
            'enterprise_customer_uuid': enterprise_customer_uuid,
            'start_date': start_date,
            'end_date': end_date,
        }

        response = self.completion_filters.enterprise_user_query_filter(
            group_uuid, enterprise_customer_uuid
        )
        if response is not None:
            enterprise_user_id_in_filter, enterprise_user_id_params = response
            query_filters.append(enterprise_user_id_in_filter)
            params.update(enterprise_user_id_params)

        # add optional filters
        if course_type:
            query_filters.append(EqualQueryFilter(
                column='course_product_line',
                value_placeholder='course_type',
            ))
            params['course_type'] = course_type

        if course_key:
            query_filters.append(EqualQueryFilter(
                column='course_key',
                value_placeholder='course_key',
            ))
            params['course_key'] = course_key

        if budget_uuid:
            query_filters.append(EqualQueryFilter(
                column='subsidy_access_policy_uuid',
                value_placeholder='budget_uuid',
            ))
            params['budget_uuid'] = budget_uuid

        return query_filters, params

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
    def get_enrollment_count(
            self,
            enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
    ) -> int:
        """
        Get the total number of enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            (int): The total number of enrollments.
        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date
        )

        results = run_query(
            query=self.queries.get_enrollment_count_query(query_filters),
            params=query_filter_params
        )
        if not results:
            return 0
        return int(results[0][0] or 0)

    @cache_it()
    def get_all_enrollments(
            self,
            enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
            limit: int,
            offset: int,
    ) -> list:
        """
        Get all enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            list<dict>: A list of dictionaries containing the enrollment data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date
        )

        return run_query(
            query=self.queries.get_all_enrollments_query(query_filters),
            params={
                **query_filter_params,
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
    def get_completion_count(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get the completion count for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            int: The completion count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_completion(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        results = run_query(
            query=self.queries.get_completion_count_query(query_filters),
            params=query_filter_params,
            as_dict=False,
        )
        # Handle empty results defensively
        if not results or not results[0] or len(results[0]) == 0:
            return 0

        return int(results[0][0] or 0)

    @cache_it()
    def get_top_courses_by_enrollments(
            self, enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ) -> list:
        """
        Get the top courses enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the course key, course_title and enrollment count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )

        return run_query(
            query=self.queries.get_top_courses_by_enrollments_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_enrollments(
            self,
            enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ) -> list:
        """
        Get the top subjects by enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the subject and enrollment count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )

        return run_query(
            query=self.queries.get_top_subjects_by_enrollments_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_enrolment_time_series_data(
            self, enterprise_customer_uuid: UUID,
            group_uuid: Optional[UUID],
            start_date: date,
            end_date: date,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ) -> list:
        """
        Get the enrollment time series data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the date and enrollment count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )

        return run_query(
            query=self.queries.get_enrolment_time_series_data_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_all_completions(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        limit: int,
        offset: int,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get all completions for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            group_uuid (UUID): The UUID of the group.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the completions data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_completion(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_all_completions_query(query_filters),
            params={
                **query_filter_params,
                'limit': limit,
                'offset': offset,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_courses_by_completions(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None
    ):
        """
        Get the top courses by completion for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the course key, course_title and completion count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_completion(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_top_courses_by_completions_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_completions(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None
    ):
        """
        Get the top subjects by completions for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the subject and completion count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_completion(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_top_subjects_by_completions_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_completions_time_series_data(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None
    ):
        """
        Get the completions time series data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the date and completion count.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_completion(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_completions_time_series_data_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_all_enrolled_courses(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        group_uuid: Optional[UUID] = None,
        course_type: Optional[str] = None,
    ):
        """
        Get all enrolled courses for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of the group.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries where each dict will contain course key and course title.

        """
        query_filters, query_filter_params = self.__get_common_query_filters(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type
        )

        return run_query(
            query=self.queries.get_enrolled_courses(query_filters),
            params=query_filter_params,
            as_dict=True,
        )
