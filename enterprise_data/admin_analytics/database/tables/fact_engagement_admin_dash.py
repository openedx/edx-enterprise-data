"""
Module for interacting with the fact_enrollment_engagement_day_admin_dash table.
"""
from datetime import date
from typing import Optional, Tuple
from uuid import UUID

from enterprise_data.admin_analytics.database.query_filters import EqualQueryFilter, INQueryFilter, NULLQueryFilter
from enterprise_data.cache.decorators import cache_it
from enterprise_data.utils import find_first

from ..filters import FactEngagementAdminDashFilters
from ..queries import FactEngagementAdminDashQueries
from ..query_filters import QueryFilters
from ..utils import run_query
from .base import BaseTable

NULL_EMAIL_TEXT = 'learners who have not shared consent'


class FactEngagementAdminDashTable(BaseTable):
    """
    Class for communicating with the fact_enrollment_engagement_day_admin_dash table.
    """
    queries = FactEngagementAdminDashQueries()
    engagement_filters = FactEngagementAdminDashFilters()

    def __get_common_query_filters_for_engagement(
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
        """
        query_filters = QueryFilters([
            self.engagement_filters.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
            self.engagement_filters.date_range_filter('activity_date', 'start_date', 'end_date'),
        ])
        params = {
            'enterprise_customer_uuid': enterprise_customer_uuid,
            'start_date': start_date,
            'end_date': end_date,
        }

        response = self.engagement_filters.enterprise_user_query_filter(
            group_uuid,
            enterprise_customer_uuid
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

    @cache_it()
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
        if not results:
            return 0.0, 0

        return tuple(results[0])

    @cache_it()
    def get_engagement_count(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date
    ):
        """
        Get the total number of engagements for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            int: The total number of engagements.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_engagement(
            enterprise_customer_uuid, group_uuid, start_date, end_date
        )

        results = run_query(
            query=self.queries.get_engagement_count_query(query_filters),
            params=query_filter_params,
        )
        if not results:
            return 0
        return results[0][0]

    @cache_it()
    def get_all_engagements(
        self,
        enterprise_customer_uuid: UUID,
        group_uuid: Optional[UUID],
        start_date: date,
        end_date: date,
        limit: int,
        offset: int
    ):
        """
        Get all engagement data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            group_uuid (UUID): The UUID of a group.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            list<dict>: A list of dictionaries containing the engagement data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_engagement(
            enterprise_customer_uuid, group_uuid, start_date, end_date
        )

        return run_query(
            query=self.queries.get_all_engagement_query(query_filters),
            params={
                **query_filter_params,
                'limit': limit,
                'offset': offset,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_courses_by_engagement(
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
        Get the top courses by user engagement for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the course data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_engagement(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_top_courses_by_engagement_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_engagement(
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
        Get the top subjects by user engagement for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the subject data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_engagement(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_top_subjects_by_engagement_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    @cache_it()
    def get_engagement_time_series_data(
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
        Get the engagement time series data.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the engagement time series data.
        """
        query_filters, query_filter_params = self.__get_common_query_filters_for_engagement(
            enterprise_customer_uuid, group_uuid, start_date, end_date, course_type, course_key, budget_uuid
        )
        return run_query(
            query=self.queries.get_engagement_time_series_data_query(query_filters),
            params=query_filter_params,
            as_dict=True,
        )

    def build_query_filters_for_leaderboard(
        self,
        enterprise_customer_uuid: UUID,
        date_column: str,
        start_date: date,
        end_date: date,
        equality_filters: Optional[dict] = None,
        null_filters: Optional[list] = None,
        in_filters: Optional[dict] = None
    ):
        """
        Build query filters and parameters for enterprise analytics queries.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date for the query.
            end_date (date): The end date for the query.
            equality_filters (dict, optional): Dictionary of column names and their values to filter by.
                Example: {'course_type': 'OCM', 'is_engaged': 1}
            null_filters (list, optional): List of columns to check for NULL or NOT NULL. Each item should be
                a dict with 'column' and 'null_check' keys.
                Example: [{'column': 'email', 'null_check': True}]
            in_filters (dict, optional): Dictionary of column names and their values to filter by using IN clause.
                Example: {'email': ['user1@example.com', 'user2@example.com']}

        Returns:
            tuple: A tuple containing:
                - QueryFilters: The filters to apply to the query.
                - dict: The parameters to use in the query.
        """
        optional_params = {}
        default_params = {
            'enterprise_customer_uuid': enterprise_customer_uuid,
            'start_date': start_date,
            'end_date': end_date,
        }

        query_filters = QueryFilters([
            self.engagement_filters.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
            self.engagement_filters.date_range_filter(
                column=date_column,
                start_date_params_key='start_date',
                end_date_params_key='end_date',
            ),
        ])

        if equality_filters:
            for column, value in equality_filters.items():
                if value is not None:
                    query_filters.append(EqualQueryFilter(
                        column=column,
                        value_placeholder=column,
                    ))
                    optional_params[column] = value

        if in_filters:
            for column, values_list in in_filters.items():
                params = {f'{column}_{index}': value for index, value in enumerate(values_list)}
                query_filters.append(INQueryFilter(
                    column=column,
                    values=values_list
                ))

        if null_filters:
            for null_column in null_filters:
                query_filters.append(NULLQueryFilter(
                    column=null_column['column'],
                    null_check=null_column['null_check']
                ))

        params = {**default_params, **optional_params}
        return query_filters, params

    @cache_it()
    def _get_engagement_data_for_leaderboard(
            self,
            enterprise_customer_uuid: UUID,
            start_date: date,
            end_date: date,
            limit: int,
            offset: int,
            include_null_email: bool,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None,
    ):
        """
        Get the engagement data for leaderboard.

        The engagement data would include fields like learning time, session length of
        the enterprise learners to show in the leaderboard.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.
            include_null_email (bool): If True, only fetch data for NULL emails.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list[dict]: The engagement data for leaderboard.
        """
        equality_filters = {
            'course_product_line': course_type,
            'course_key': course_key,
            'subsidy_access_policy_uuid': budget_uuid,
            'is_engaged': 1
        }
        query_filters, params = self.build_query_filters_for_leaderboard(
            enterprise_customer_uuid=enterprise_customer_uuid,
            date_column='activity_date',
            start_date=start_date,
            end_date=end_date,
            equality_filters=equality_filters,
        )
        engagements = run_query(
            query=self.queries.get_engagement_data_for_leaderboard_query(query_filters),
            params={
                **params,
                **{
                    'limit': limit,
                    'offset': offset,
                }
            },
            as_dict=True,
        )

        if include_null_email:
            null_filters = [{
                'column': 'email',
                'null_check': True
            }]
            query_filters, params = self.build_query_filters_for_leaderboard(
                enterprise_customer_uuid=enterprise_customer_uuid,
                date_column='activity_date',
                start_date=start_date,
                end_date=end_date,
                equality_filters=equality_filters,
                null_filters=null_filters
            )

            engagement_for_null_email = run_query(
                query=self.queries.get_engagement_data_for_leaderboard_null_email_only_query(query_filters),
                params=params,
                as_dict=True,
            )
            engagements += engagement_for_null_email
        return engagements

    @cache_it()
    def _get_completion_data_for_leaderboard_query(
            self,
            enterprise_customer_uuid: UUID,
            start_date: date,
            end_date: date,
            email_list: list,
            include_null_email: bool,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ):
        """
        Get the completion data for leaderboard.

        The completion data would include fields like course completion count of enterprise learners of the
        given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            email_list (list<str>): List of emails of the enterprise learners.
            include_null_email (bool): If True, only fetch data for NULL emails.
            course_type (Optional[str]): The course type (OCM or Executive Education) to filter by (optional).
            course_key (Optional[str]): The course key to filter by (optional).
            budget_uuid (Optional[str]): The budget UUID to filter by (optional).

        Returns:
            list[dict]: The engagement data for leaderboard.
        """
        equality_filters = {
            'course_product_line': course_type,
            'course_key': course_key,
            'subsidy_access_policy_uuid': budget_uuid,
            'has_passed': 1
        }
        in_filters = {
            'email': email_list
        }
        query_filters, params = self.build_query_filters_for_leaderboard(
            enterprise_customer_uuid=enterprise_customer_uuid,
            date_column='passed_date',
            start_date=start_date,
            end_date=end_date,
            equality_filters=equality_filters,
            in_filters=in_filters,
        )

        completions = run_query(
            query=self.queries.get_completion_data_for_leaderboard_query(query_filters),
            params=params,
            as_dict=True,
        )

        if include_null_email:
            query_filters, params = self.build_query_filters_for_leaderboard(
                enterprise_customer_uuid=enterprise_customer_uuid,
                date_column='passed_date',
                start_date=start_date,
                end_date=end_date,
                equality_filters=equality_filters,
                null_filters=[{'column': 'email', 'null_check': True}]
            )
            completions_for_null_email = run_query(
                query=self.queries.get_completion_data_for_leaderboard_null_email_only_query(query_filters),
                params=params,
                as_dict=True,
            )
            completions += completions_for_null_email

        return completions

    def get_all_leaderboard_data(
            self,
            enterprise_customer_uuid: UUID,
            start_date: date,
            end_date: date,
            limit: int,
            offset: int,
            total_count: int,
            course_type: Optional[str] = None,
            course_key: Optional[str] = None,
            budget_uuid: Optional[str] = None
    ):
        """
        Get the leaderboard data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.
            total_count (int): The total number of records.
            course_type (Optional[str]): The course type filter.
            course_key (Optional[str]): The course key filter.
            budget_uuid (Optional[str]): The budget UUID filter.

        Returns:
            list[dict]: The leaderboard data.
        """
        include_null_email = False
        # If this is the last or only page, we need to include NULL emails record.
        if total_count <= offset + limit:
            include_null_email = True

        engagement_data = self._get_engagement_data_for_leaderboard(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            include_null_email=include_null_email,
            course_type=course_type,
            course_key=course_key,
            budget_uuid=budget_uuid,
        )
        # If there is no data, no need to proceed.
        if not engagement_data:
            return []

        engagement_data_dict = {
            engagement['email']: engagement for engagement in engagement_data if engagement['email']
        }
        completion_data = self._get_completion_data_for_leaderboard_query(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            email_list=list(engagement_data_dict.keys()),
            include_null_email=include_null_email,
            course_type=course_type,
            course_key=course_key,
            budget_uuid=budget_uuid,
        )
        for completion in completion_data:
            email = completion['email']
            engagement_data_dict[email]['course_completion_count'] = completion['course_completion_count']

        if include_null_email:
            engagement_data_dict['None'] = find_first(engagement_data, lambda x: x['email'] is None) or {}
            completion = find_first(completion_data, lambda x: x['email'] is None) or \
                {'course_completion_count': ''}
            engagement_data_dict['None']['course_completion_count'] = completion['course_completion_count']
            engagement_data_dict['None']['email'] = NULL_EMAIL_TEXT

        return list(engagement_data_dict.values())

    @cache_it()
    def get_leaderboard_data_count(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None
    ):
        """
        Get the total number of leaderboard records for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (Optional[str]): The course type filter.
            course_key (Optional[str]): The course key filter.
            budget_uuid (Optional[str]): The budget UUID filter.

        Returns:
            (int): The total number of leaderboard records.
        """
        equality_filters = {
            'course_product_line': course_type,
            'course_key': course_key,
            'subsidy_access_policy_uuid': budget_uuid,
            'is_engaged': 1
        }
        query_filters, params = self.build_query_filters_for_leaderboard(
            enterprise_customer_uuid=enterprise_customer_uuid,
            date_column='activity_date',
            start_date=start_date,
            end_date=end_date,
            equality_filters=equality_filters,
        )

        results = run_query(
            query=self.queries.get_leaderboard_data_count_query(query_filters),
            params=params
        )
        if not results:
            return 0
        return results[0][0]
