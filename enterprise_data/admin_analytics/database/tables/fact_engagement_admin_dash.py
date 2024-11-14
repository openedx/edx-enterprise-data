"""
Module for interacting with the fact_enrollment_engagement_day_admin_dash table.
"""
from datetime import date
from uuid import UUID

from enterprise_data.cache.decorators import cache_it
from enterprise_data.utils import find_first

from ..queries import FactEngagementAdminDashQueries
from ..utils import run_query
from .base import BaseTable

NULL_EMAIL_TEXT = 'learners who have not shared consent'


class FactEngagementAdminDashTable(BaseTable):
    """
    Class for communicating with the fact_enrollment_engagement_day_admin_dash table.
    """
    queries = FactEngagementAdminDashQueries()

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
    def get_engagement_count(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the total number of engagements for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            int: The total number of engagements.
        """
        results = run_query(
            query=self.queries.get_engagement_count_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        if not results:
            return 0
        return results[0][0]

    @cache_it()
    def get_all_engagements(
            self, enterprise_customer_uuid: UUID, start_date: date, end_date: date, limit: int, offset: int
    ):
        """
        Get all engagement data for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            list<dict>: A list of dictionaries containing the engagement data.
        """
        return run_query(
            query=self.queries.get_all_engagement_query(),
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
    def get_top_courses_by_engagement(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top courses by user engagement for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the course data.
        """
        return run_query(
            query=self.queries.get_top_courses_by_engagement_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_subjects_by_engagement(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top subjects by user engagement for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the subject data.
        """
        return run_query(
            query=self.queries.get_top_subjects_by_engagement_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_engagement_time_series_data(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the engagement time series data.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the engagement time series data.
        """
        return run_query(
            query=self.queries.get_engagement_time_series_data_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def _get_engagement_data_for_leaderboard(
            self,
            enterprise_customer_uuid: UUID,
            start_date: date,
            end_date: date,
            limit: int,
            offset: int,
            include_null_email: bool,

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

        Returns:
            list[dict]: The engagement data for leaderboard.
        """
        engagements = run_query(
            query=self.queries.get_engagement_data_for_leaderboard_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
                'offset': offset,
            },
            as_dict=True,
        )

        if include_null_email:
            engagement_for_null_email = run_query(
                query=self.queries.get_engagement_data_for_leaderboard_null_email_only_query(),
                params={
                    'enterprise_customer_uuid': enterprise_customer_uuid,
                    'start_date': start_date,
                    'end_date': end_date,
                },
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

        Returns:
            list[dict]: The engagement data for leaderboard.
        """

        completions = run_query(
            query=self.queries.get_completion_data_for_leaderboard_query(email_list),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

        if include_null_email:
            completions_for_null_email = run_query(
                query=self.queries.get_completion_data_for_leaderboard_null_email_only_query(),
                params={
                    'enterprise_customer_uuid': enterprise_customer_uuid,
                    'start_date': start_date,
                    'end_date': end_date,
                },
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
    def get_leaderboard_data_count(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the total number of leaderboard records for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            (int): The total number of leaderboard records.
        """
        results = run_query(
            query=self.queries.get_leaderboard_data_count_query(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        if not results:
            return 0
        return results[0][0]
