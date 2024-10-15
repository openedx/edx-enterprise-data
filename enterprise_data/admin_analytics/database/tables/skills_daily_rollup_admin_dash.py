"""
Module for interacting with the skills_daily_rollup_admin_dash table.
"""
from datetime import date
from uuid import UUID

from enterprise_data.admin_analytics.database.queries.skills_daily_rollup_admin_dash import (
    SkillsDailyRollupAdminDashQueries,
)
from enterprise_data.admin_analytics.database.tables.base import BaseTable
from enterprise_data.admin_analytics.database.utils import run_query
from enterprise_data.cache.decorators import cache_it


class SkillsDailyRollupAdminDashTable(BaseTable):
    """
    Class for communicating with the skills_daily_rollup_admin_dash table.
    """
    queries = SkillsDailyRollupAdminDashQueries()

    @cache_it()
    def get_top_skills(self, enterprise_customer_uuid: UUID, start_date: date, end_date: date):
        """
        Get the top skills for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, skill_type, enrolls and completions.
        """
        return run_query(
            query=self.queries.get_top_skills(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_skills_by_enrollment(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date
    ):
        """
        Get the top skills by enrollments for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, subject_name, count.
        """
        return run_query(
            query=self.queries.get_top_skills_by_enrollment(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )

    @cache_it()
    def get_top_skills_by_completion(
        self,
        enterprise_customer_uuid: UUID,
        start_date: date,
        end_date: date
    ):
        """
        Get the top skills by completion for the given enterprise customer.

        Arguments:
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.
            start_date (date): The start date.
            end_date (date): The end date.

        Returns:
            list<dict>: A list of dictionaries containing the skill_name, subject_name, count.
        """
        return run_query(
            query=self.queries.get_top_skills_by_completion(),
            params={
                'enterprise_customer_uuid': enterprise_customer_uuid,
                'start_date': start_date,
                'end_date': end_date,
            },
            as_dict=True,
        )
