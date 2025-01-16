"""
Module containing queries for the skills_daily_rollup_admin_dash table.
"""


class SkillsDailyRollupAdminDashQueries:
    """
    Queries related to the skills_daily_rollup_admin_dash table.
    """
    @staticmethod
    def get_top_skills():
        """
        Get the query to fetch the top skills for an enterprise customer.
        """
        return """
            SELECT
                skill_name,
                skill_type,
                SUM(enrolls) AS enrolls,
                SUM(completions) AS completions
            FROM
                skills_daily_rollup_admin_dash
            WHERE
                enterprise_customer_uuid=%(enterprise_customer_uuid)s AND
                date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY
                skill_name, skill_type
            ORDER BY
                enrolls DESC, completions DESC;
        """

    @staticmethod
    def get_top_skills_by_enrollment():
        """
        Get the query to fetch the top skills by enrollment for an enterprise customer.
        """
        return """
            WITH TopSkills AS (
                -- Get top 10 skills by total enrollments
                SELECT
                    skill_name,
                    SUM(enrolls) AS total_enrollment_count
                FROM
                    skills_daily_rollup_admin_dash
                WHERE
                    enterprise_customer_uuid=%(enterprise_customer_uuid)s
                    AND date BETWEEN %(start_date)s AND %(end_date)s
                GROUP BY
                    skill_name
                ORDER BY
                    total_enrollment_count DESC
                LIMIT 10
            )
            SELECT
                sd.skill_name,
                CASE
                    WHEN sd.primary_subject_name IN (
                        'business-management', 'computer-science',
                        'data-analysis-statistics', 'engineering', 'communication'
                    ) THEN sd.primary_subject_name
                    ELSE 'other'
                END AS subject_name,
                SUM(sd.enrolls) AS count
            FROM
                skills_daily_rollup_admin_dash AS sd
            JOIN
                TopSkills AS ts ON sd.skill_name = ts.skill_name
            WHERE
                sd.enterprise_customer_uuid=%(enterprise_customer_uuid)s
                AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY
                sd.skill_name, subject_name
            ORDER BY
                total_enrollment_count DESC;
        """

    @staticmethod
    def get_top_skills_by_completion():
        """
        Get the query to fetch the top skills by completion for an enterprise customer.
        """
        return """
            WITH TopSkills AS (
                -- Get top 10 skills by total completions
                SELECT
                    skill_name,
                    SUM(completions) AS total_completion_count
                FROM
                    skills_daily_rollup_admin_dash
                WHERE
                    enterprise_customer_uuid=%(enterprise_customer_uuid)s
                    AND date BETWEEN %(start_date)s AND %(end_date)s
                GROUP BY
                    skill_name
                ORDER BY
                    total_completion_count DESC
                LIMIT 10
            )
            SELECT
                sd.skill_name,
                CASE
                    WHEN sd.primary_subject_name IN (
                        'business-management', 'computer-science',
                        'data-analysis-statistics', 'engineering', 'communication'
                    ) THEN sd.primary_subject_name
                    ELSE 'other'
                END AS subject_name,
                SUM(sd.completions) AS count
            FROM
                skills_daily_rollup_admin_dash AS sd
            JOIN
                TopSkills AS ts ON sd.skill_name = ts.skill_name
            WHERE
                sd.enterprise_customer_uuid=%(enterprise_customer_uuid)s
                AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY
                sd.skill_name, subject_name
            ORDER BY
                total_completion_count DESC;
        """
