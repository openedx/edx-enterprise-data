"""
Module for interacting with the skills_daily_rollup_admin_dash table.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from enterprise_data.admin_analytics.database.filters.mixins import CommonFiltersMixin
from enterprise_data.admin_analytics.database.queries.skills_daily_rollup_admin_dash import (
    SkillsDailyRollupAdminDashQueries,
)
from enterprise_data.admin_analytics.database.query_filters import EqualQueryFilter
from enterprise_data.admin_analytics.database.tables.base import BaseTable
from enterprise_data.admin_analytics.database.utils import run_query
from enterprise_data.cache.decorators import cache_it

from ..query_filters import QueryFilters


class SkillsDailyRollupAdminDashTable(CommonFiltersMixin, BaseTable):
    """
    Class for communicating with the skills_daily_rollup_admin_dash table.
    """
    queries = SkillsDailyRollupAdminDashQueries()

    def build_query_filters(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Build query filters and parameters for enterprise analytics queries.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date for the query.
            end_date (date): The end date for the query.
            course_type (str, optional): The course type to filter by (e.g., 'OCM', 'Executive Education').
            course_key (str, optional): The course key to filter by.
            budget_uuid (str, optional): The budget UUID to filter by.

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
            self.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
            self.date_range_filter(
                column='date',
                start_date_params_key='start_date',
                end_date_params_key='end_date',
            ),
        ])

        if course_key:
            query_filters.append(EqualQueryFilter(
                column='course_key',
                value_placeholder='course_key',
            ))
            optional_params['course_key'] = course_key

        if course_type:
            query_filters.append(EqualQueryFilter(
                column='course_product_line',
                value_placeholder='course_type',
            ))
            optional_params['course_type'] = course_type

        if budget_uuid:
            query_filters.append(EqualQueryFilter(
                column='subsidy_access_policy_uuid',
                value_placeholder='budget_uuid',
            ))
            optional_params['budget_uuid'] = budget_uuid

        params = {**default_params, **optional_params}
        return query_filters, params

    @cache_it()
    def get_top_skills(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get the top skills for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional).
            budget_uuid (str): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, skill_type, enrolls and completions.
        """
        query_filters, params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_type=course_type,
            course_key=course_key,
            budget_uuid=budget_uuid,
        )
        return run_query(
            query=self.queries.get_top_skills(query_filters),
            params=params,
            as_dict=True,
        )

    @cache_it()
    def get_top_skills_by_enrollment(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get the top skills by enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional).
            budget_uuid (str): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, subject_name, count.
        """
        query_filters, params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_type=course_type,
            course_key=course_key,
            budget_uuid=budget_uuid,
        )
        return run_query(
            query=self.queries.get_top_skills_by_enrollment(query_filters),
            params=params,
            as_dict=True,
        )

    @cache_it()
    def get_top_skills_by_completion(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get the top skills by completion for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional).
            budget_uuid (str): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, subject_name, count.
        """
        query_filters, params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_type=course_type,
            course_key=course_key,
            budget_uuid=budget_uuid,
        )
        return run_query(
            query=self.queries.get_top_skills_by_completion(query_filters),
            params=params,
            as_dict=True,
        )

    def get_skills_by_learning_hours(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_key: Optional[str] = None,
        course_type: Optional[str] = None,
        budget_uuid: Optional[str] = None,
    ):
        """
        Get the skills by learning hours for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_key (str): The course key to filter by (optional).
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            budget_uuid (str): The budget UUID to filter by (optional).

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, subject_name, count.
        """
        query_filters, params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
        )
        return run_query(
            query=self.queries.get_skills_by_learning_hours(query_filters),
            params=params,
            as_dict=True,
        )
