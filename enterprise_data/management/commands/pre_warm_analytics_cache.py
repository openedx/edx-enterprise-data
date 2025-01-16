"""
Management command for pre-warming the analytics cache for large enterprises.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from enterprise_data.admin_analytics.database.tables import (
    FactEngagementAdminDashTable,
    FactEnrollmentAdminDashTable,
    SkillsDailyRollupAdminDashTable,
)


class Command(BaseCommand):
    """
    Add cache entries for analytics related data for a large enterprise.

    The top enterprises will be the ones with the most enrollments.
    """
    help = 'Pre-warm the analytics cache for a large enterprises.'

    @staticmethod
    def __cache_enrollment_data(enterprise_customer_uuid):
        """
        Helper method to cache all the enrollment related data for the given enterprise.

        Arguments:
            enterprise_customer_uuid (str): The UUID of the enterprise customer.
        """
        enterprise_enrollment_table = FactEnrollmentAdminDashTable()
        start_date, _ = enterprise_enrollment_table.get_enrollment_date_range(
            enterprise_customer_uuid,
        )
        end_date = date.today()
        enterprise_enrollment_table.get_enrollment_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        page_size = 100
        enterprise_enrollment_table.get_all_enrollments(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=0,
        )
        enterprise_enrollment_table.get_enrollment_and_course_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_completion_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_top_courses_by_enrollments(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_top_subjects_by_enrollments(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_enrolment_time_series_data(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def __cache_completions_data(enterprise_customer_uuid):
        """
        Helper method to cache all the completions related data for the given enterprise.

        Arguments:
            enterprise_customer_uuid (str): The UUID of the enterprise customer.
        """
        enterprise_enrollment_table = FactEnrollmentAdminDashTable()
        start_date, _ = enterprise_enrollment_table.get_enrollment_date_range(
            enterprise_customer_uuid,
        )
        end_date = date.today()

        page_size = 100
        enterprise_enrollment_table.get_all_completions(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=0,
        )
        enterprise_enrollment_table.get_completion_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_top_courses_by_completions(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_top_subjects_by_completions(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_enrollment_table.get_completions_time_series_data(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def __cache_engagement_data(enterprise_customer_uuid):
        """
        Helper method to cache all the engagement related data for the given enterprise.

        Arguments:
            enterprise_customer_uuid (str): The UUID of the enterprise customer.
        """
        start_date, _ = FactEnrollmentAdminDashTable().get_enrollment_date_range(
            enterprise_customer_uuid,
        )
        end_date = date.today()
        enterprise_engagement_table = FactEngagementAdminDashTable()
        enterprise_engagement_table.get_learning_hours_and_daily_sessions(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_engagement_table.get_engagement_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        page_size = 100
        enterprise_engagement_table.get_all_engagements(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=0,
        )
        enterprise_engagement_table.get_top_courses_by_engagement(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_engagement_table.get_top_subjects_by_engagement(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_engagement_table.get_engagement_time_series_data(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        total_count = enterprise_engagement_table.get_leaderboard_data_count(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        enterprise_engagement_table.get_all_leaderboard_data(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=0,
            total_count=total_count,
        )

    @staticmethod
    def __cache_skills_data(enterprise_customer_uuid):
        """
        Helper method to cache all the skills related data for the given enterprise.

        Arguments:
            enterprise_customer_uuid (str): The UUID of the enterprise customer.
        """
        start_date, _ = FactEnrollmentAdminDashTable().get_enrollment_date_range(
            enterprise_customer_uuid,
        )
        end_date = date.today()
        skills_table = SkillsDailyRollupAdminDashTable()
        skills_table.get_top_skills(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        skills_table.get_top_skills_by_enrollment(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )
        skills_table.get_top_skills_by_completion(
            enterprise_customer_uuid=enterprise_customer_uuid,
            start_date=start_date,
            end_date=end_date,
        )

    def handle(self, *args, **options):
        for enterprise_customer_uuid in FactEnrollmentAdminDashTable().get_top_enterprises():
            try:
                self.__cache_enrollment_data(enterprise_customer_uuid)
                self.__cache_completions_data(enterprise_customer_uuid)
                self.__cache_engagement_data(enterprise_customer_uuid)
                self.__cache_skills_data(enterprise_customer_uuid)
            except Exception as exc:
                info = (
                    'Error trying to add cache entries for enterprise '
                    '{}: {}'.format(enterprise_customer_uuid, exc)
                )
                raise CommandError(info) from exc
