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
from enterprise_data.admin_analytics.database.query_filters import ComparisonQueryFilter, EqualQueryFilter
from enterprise_data.admin_analytics.database.tables.base import BaseTable
from enterprise_data.admin_analytics.database.tables.fact_enrollment_admin_dash import FactEnrollmentAdminDashTable
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
        include_date_range_filter: Optional[bool] = True,
        group_uuid: Optional[UUID] = None,
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
            include_date_range_filter (bool, optional): Whether to include the date range filter. Defaults to True.
            group_uuid (UUID, optional): The group UUID to filter by. Defaults to None.

        Returns:
            tuple: A tuple containing:
                - QueryFilters: The filters to apply to the query.
                - dict: The parameters to use in the query.
        """
        optional_params = {}
        default_params = {
            'enterprise_customer_uuid': enterprise_customer_uuid,
        }

        query_filters = QueryFilters([
            self.enterprise_customer_uuid_filter('enterprise_customer_uuid'),
        ])

        if include_date_range_filter is True:
            query_filters.append(
                self.date_range_filter(
                    column='date',
                    start_date_params_key='start_date',
                    end_date_params_key='end_date',
                )
            )
            default_params.update({
                'start_date': start_date,
                'end_date': end_date,
            })

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

        # See https://2u-internal.atlassian.net/browse/DPMF-994?focusedCommentId=5688616 for context on default value
        default_group_uuid = '00000000000000000000000000000000'
        group_uuid_value = group_uuid or default_group_uuid
        query_filters.append(EqualQueryFilter(
            column='enterprise_group_uuid',
            value_placeholder='enterprise_group_uuid',
        ))
        optional_params['enterprise_group_uuid'] = group_uuid_value

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
        group_uuid: Optional[str] = None,
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
            group_uuid (str): The group UUID to filter by (optional).

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
            group_uuid=group_uuid,
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
        group_uuid: Optional[str] = None,
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
            group_uuid (str): The group UUID to filter by (optional).

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
            group_uuid=group_uuid,
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
        group_uuid: Optional[str] = None,
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
            group_uuid (str): The group UUID to filter by (optional).

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
            group_uuid=group_uuid,
        )
        return run_query(
            query=self.queries.get_top_skills_by_completion(query_filters),
            params=params,
            as_dict=True,
        )

    @cache_it()
    def get_skills_by_learning_hours(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_key: Optional[str] = None,
        course_type: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
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
            group_uuid (str): The group UUID to filter by (optional).

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
            group_uuid=group_uuid,
        )
        return run_query(
            query=self.queries.get_skills_by_learning_hours(query_filters),
            params=params,
            as_dict=True,
        )

    @cache_it()
    def get_unique_skills_gained(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
    ):
        """
        Get the unique skills gained for the given enterprise customer.

        Args:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional). Defaults to None.
            budget_uuid (str): The budget UUID to filter by (optional). Defaults to None.
            group_uuid (str): The group UUID to filter by (optional). Defaults to None.
        """
        query_filters, params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            group_uuid=group_uuid,
        )

        query_filters.append(ComparisonQueryFilter(
            column='completions',
            operator='>',
            value=0
        ))

        results = run_query(
            query=self.queries.get_unique_skills_gained(query_filters),
            params=params,
        )

        return results[0][0] if results else 0

    def construct_upskill_learners_query_filters(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
    ):
        """
        Construct query filters and parameters for upskilled learners query.

        Args:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional). Defaults to None.
            budget_uuid (str): The budget UUID to filter by (optional). Defaults to None.
            group_uuid (str): The group UUID to filter by (optional). Defaults to None.
        """
        skills_query_filters, skills_params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            group_uuid=group_uuid,
        )
        skills_query_filters.append(ComparisonQueryFilter(
            column='completions',
            operator='>',
            value=0
        ))

        enrollment_query_filters, enrollment_params = FactEnrollmentAdminDashTable().build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
        )
        enrollment_query_filters.append(ComparisonQueryFilter(
            column='has_passed',
            operator='=',
            value=1
        ))

        return skills_query_filters, skills_params, enrollment_query_filters, enrollment_params

    @cache_it()
    def get_upskilled_learners_count(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
    ):
        """
        Get the count of upskilled learners for the given enterprise customer.

        Args:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional). Defaults to None.
            budget_uuid (str): The budget UUID to filter by (optional). Defaults to None.
            group_uuid (str): The group UUID to filter by (optional). Defaults to None.
        """
        skills_filters, skills_params, enroll_filters, enroll_params = self.construct_upskill_learners_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            group_uuid=group_uuid,
        )

        results = run_query(
            query=self.queries.get_upskilled_learners_count(skills_filters, enroll_filters),
            params={**skills_params, **enroll_params},
        )

        return results[0][0] if results else 0

    def construct_new_skills_learned_query_filters(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
    ):
        """
        Construct query filters and parameters for new skills learned query.

        Args:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional). Defaults to None.
            budget_uuid (str): The budget UUID to filter by (optional). Defaults to None.
            group_uuid (str): The group UUID to filter by (optional). Defaults to None.
        """
        common_query_filters = QueryFilters([
            ComparisonQueryFilter(
                column='completions',
                operator='>',
                value=0
            ),
            ComparisonQueryFilter(
                column='confidence',
                operator='>=',
                value=0.8
            )
        ])

        current_skills_filters, current_skills_params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            group_uuid=group_uuid,
        )
        current_skills_filters.extend(common_query_filters)

        historical_skills_filters, hist_skills_params = self.build_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            include_date_range_filter=False,
        )
        historical_skills_filters.append(
            ComparisonQueryFilter(
                column='date',
                operator='<',
                value_placeholder='start_date'
            )
        )
        historical_skills_filters.extend(common_query_filters)

        return current_skills_filters, current_skills_params, historical_skills_filters, hist_skills_params

    @cache_it()
    def get_new_skills_learned_count(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None,
        course_key: Optional[str] = None,
        budget_uuid: Optional[str] = None,
        group_uuid: Optional[str] = None,
    ):
        """
        Get the count of new skills learned for the given enterprise customer.

        Args:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.
            course_type (str): The course type (OCM or Executive Education) to filter by (optional).
            course_key (str): The course key to filter by (optional). Defaults to None.
            budget_uuid (str): The budget UUID to filter by (optional). Defaults to None.
            group_uuid (str): The group UUID to filter by (optional). Defaults to None.
        """
        current_filters, current_params, hist_filters, hist_params = self.construct_new_skills_learned_query_filters(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            course_key=course_key,
            course_type=course_type,
            budget_uuid=budget_uuid,
            group_uuid=group_uuid,
        )

        results = run_query(
            query=self.queries.get_new_skills_learned_count(hist_filters, current_filters),
            params={**current_params, **hist_params},
        )

        return results[0][0] if results else 0
