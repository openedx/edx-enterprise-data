"""
Module containing queries for the skills_daily_rollup_admin_dash table.
"""
from ..query_filters import QueryFilters


class SkillsDailyRollupAdminDashQueries:
    """
    Queries related to the skills_daily_rollup_admin_dash table.
    """
    @staticmethod
    def get_top_skills(query_filters: QueryFilters):
        """
        Get the query to fetch the top skills for an enterprise customer.
        """
        return f"""
            SELECT
                skill_name,
                skill_type,
                SUM(enrolls) AS enrolls,
                SUM(completions) AS completions
            FROM
                skills_daily_rollup_admin_dash
            WHERE
                {query_filters.to_sql()}
            GROUP BY
                skill_name, skill_type
            ORDER BY
                enrolls DESC, completions DESC;
        """

    @staticmethod
    def get_top_skills_by_enrollment(query_filters: QueryFilters):
        """
        Get the query to fetch the top skills by enrollment for an enterprise customer.
        """
        return f"""
            WITH FilteredData AS (
                SELECT
                    skill_name,
                    primary_subject_name,
                    enrolls
                FROM
                    skills_daily_rollup_admin_dash
                WHERE
                    {query_filters.to_sql()}
            ),
            TopSkills AS (
                SELECT
                    skill_name,
                    SUM(enrolls) AS total_enrollment_count
                FROM
                    FilteredData
                GROUP BY
                    skill_name
                ORDER BY
                    total_enrollment_count DESC
                LIMIT 10
            )
            SELECT
                fd.skill_name,
                CASE
                    WHEN fd.primary_subject_name IN (
                        'business-management', 'computer-science',
                        'data-analysis-statistics', 'engineering', 'communication'
                    ) THEN fd.primary_subject_name
                    ELSE 'other'
                END AS subject_name,
                SUM(fd.enrolls) AS count
            FROM
                FilteredData fd
            JOIN
                TopSkills ts ON fd.skill_name = ts.skill_name
            GROUP BY
                fd.skill_name, subject_name
            ORDER BY
                ts.total_enrollment_count DESC;
        """

    @staticmethod
    def get_top_skills_by_completion(query_filters: QueryFilters):
        """
        Get the query to fetch the top skills by completion for an enterprise customer.
        """
        return f"""
            WITH FilteredData AS (
                SELECT
                    skill_name,
                    primary_subject_name,
                    completions
                FROM
                    skills_daily_rollup_admin_dash
                WHERE
                    {query_filters.to_sql()}
            ),
            TopSkills AS (
                -- Get top 10 skills by total completions
                SELECT
                    skill_name,
                    SUM(completions) AS total_completion_count
                FROM
                    FilteredData
                GROUP BY
                    skill_name
                ORDER BY
                    total_completion_count DESC
                LIMIT 10
            )
            SELECT
                fd.skill_name,
                CASE
                    WHEN fd.primary_subject_name IN (
                        'business-management', 'computer-science',
                        'data-analysis-statistics', 'engineering', 'communication'
                    ) THEN fd.primary_subject_name
                    ELSE 'other'
                END AS subject_name,
                SUM(fd.completions) AS count
            FROM
                FilteredData AS fd
            JOIN
                TopSkills AS ts ON fd.skill_name = ts.skill_name
            GROUP BY
                fd.skill_name, subject_name
            ORDER BY
                ts.total_completion_count DESC;
        """

    @staticmethod
    def get_skills_by_learning_hours(query_filters: QueryFilters, record_count: int = 25):
        """
        Get the query to fetch skills by learning hours for an enterprise customer.
        """
        return f"""
            WITH filtered_data AS (
                SELECT
                    skill_name,
                    total_learning_time_hours
                FROM
                    skills_daily_rollup_admin_dash
                WHERE
                    {query_filters.to_sql()}
            )

            SELECT
                skill_name,
                SUM(total_learning_time_hours) AS learning_hours
            FROM
                filtered_data
            GROUP BY
                skill_name
            ORDER BY
                learning_hours DESC
            LIMIT {record_count};
        """
