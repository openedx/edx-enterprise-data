"""
Utility functions for fetching data from the database.
"""
from logging import getLogger

import numpy
import pandas

from django.http import Http404

from enterprise_data.admin_analytics.database import run_query
from enterprise_data.utils import timer

LOGGER = getLogger(__name__)


def get_select_query(table: str, columns: list, enterprise_uuid: str) -> str:
    """
    Generate a SELECT query for the given table and columns.

    Arguments:
        table (str): The table to query.
        columns (list): The columns to select.
        enterprise_uuid (str): The UUID of the enterprise customer.

    Returns:
        (str): The SELECT query.
    """
    return f'SELECT {", ".join(columns)} FROM {table} WHERE enterprise_customer_uuid = "{enterprise_uuid}"'


def fetch_enrollment_data(enterprise_uuid: str):
    """
    Fetch enrollment data from the database for the given enterprise customer.

    Arguments:
        enterprise_uuid (str): The UUID of the enterprise customer.

    Returns:
        (pandas.DataFrame): The enrollment data.
    """
    enterprise_uuid = enterprise_uuid.replace('-', '')

    columns = [
        'enterprise_customer_name',
        'enterprise_customer_uuid',
        'lms_enrollment_id',
        'user_id',
        'email',
        'course_key',
        'courserun_key',
        'course_id',
        'course_subject',
        'course_title',
        'enterprise_enrollment_date',
        'lms_enrollment_mode',
        'enroll_type',
        'program_title',
        'date_certificate_awarded',
        'grade_percent',
        'cert_awarded',
        'date_certificate_created_raw',
        'passed_date_raw',
        'passed_date',
        'has_passed',
    ]
    query = get_select_query(
        table='fact_enrollment_admin_dash',
        columns=columns,
        enterprise_uuid=enterprise_uuid,
    )

    with timer('fetch_enrollment_data'):
        results = run_query(query=query)

    if not results:
        raise Http404(f'No enrollment data found for enterprise {enterprise_uuid}')

    LOGGER.info(f'[PLOTLY] Enrollment data fetched successfully. Records: {len(results)}')
    enrollments = pandas.DataFrame(numpy.array(results), columns=columns)
    LOGGER.info('[PLOTLY] Enrollment data converted to DataFrame.')

    # Convert date columns to datetime.
    enrollments['enterprise_enrollment_date'] = enrollments['enterprise_enrollment_date'].astype('datetime64[ns]')
    enrollments['date_certificate_awarded'] = enrollments['date_certificate_awarded'].astype('datetime64[ns]')
    enrollments['date_certificate_created_raw'] = enrollments['date_certificate_created_raw'].astype('datetime64[ns]')
    enrollments['passed_date_raw'] = enrollments['passed_date_raw'].astype('datetime64[ns]')
    enrollments['passed_date'] = enrollments['passed_date'].astype('datetime64[ns]')

    return enrollments


def fetch_engagement_data(enterprise_uuid: str):
    """
    Fetch engagement data from the database for the given enterprise customer.

    Arguments:
        enterprise_uuid (str): The UUID of the enterprise customer.

    Returns:
        (pandas.DataFrame): The engagement data.
    """
    enterprise_uuid = enterprise_uuid.replace('-', '')

    columns = [
        'user_id',
        'email',
        'enterprise_customer_uuid',
        'course_key',
        'enroll_type',
        'activity_date',
        'course_title',
        'course_subject',
        'is_engaged',
        'is_engaged_video',
        'is_engaged_forum',
        'is_engaged_problem',
        'is_active',
        'learning_time_seconds',
    ]
    query = get_select_query(
        table='fact_enrollment_engagement_day_admin_dash', columns=columns, enterprise_uuid=enterprise_uuid
    )

    with timer('fetch_engagement_data'):
        results = run_query(query=query)
    if not results:
        raise Http404(f'No engagement data found for enterprise {enterprise_uuid}')

    LOGGER.info(f'[PLOTLY] Engagement data fetched successfully. Records: {len(results)}')
    engagement = pandas.DataFrame(numpy.array(results), columns=columns)
    LOGGER.info('[PLOTLY] Engagement data converted to DataFrame.')
    engagement['activity_date'] = engagement['activity_date'].astype('datetime64[ns]')

    return engagement


def fetch_max_enrollment_datetime():
    """
    Fetch the latest created date from the enterprise_learner_enrollment table.

    created will be same for all records as this is added at the time of data load. Which is when the async process
    populates the data in the table. We can use this to get the latest data load time.
    """
    query = "SELECT MAX(created) FROM enterprise_learner_enrollment"
    results = run_query(query)
    if not results:
        return None
    return pandas.to_datetime(results[0][0])


def fetch_skills_data(enterprise_uuid: str):
    """
    Fetch skills data from the database for the given enterprise customer.

    Arguments:
        enterprise_uuid (str): The UUID of the enterprise customer.

    Returns:
        (pandas.DataFrame): The skills data.
    """

    enterprise_uuid = enterprise_uuid.replace('-', '')

    cols = [
        'course_number',
        'skill_type',
        'skill_name',
        'skill_url',
        'confidence',
        'skill_rank',
        'course_title',
        'course_key',
        'level_type',
        'primary_subject_name',
        'date',
        'enterprise_customer_uuid',
        'enterprise_customer_name',
        'enrolls',
        'completions',
    ]
    query = get_select_query(
        table='skills_daily_rollup_admin_dash', columns=cols, enterprise_uuid=enterprise_uuid
    )

    with timer('fetch_skills_data'):
        skills = run_query(query=query)

    if not skills:
        raise Http404(f'No skills data found for enterprise {enterprise_uuid}')

    LOGGER.info(f'[PLOTLY] Skills data fetched successfully. Records: {len(skills)}')
    skills = pandas.DataFrame(numpy.array(skills), columns=cols)
    LOGGER.info('[PLOTLY] Skills data converted to DataFrame.')
    skills['date'] = skills['date'].astype('datetime64[ns]')

    return skills
