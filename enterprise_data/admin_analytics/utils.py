"""
Utility functions for fetching data from the database.
"""
from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger

from edx_django_utils.cache import TieredCache, get_cache_key

from enterprise_data.admin_analytics.constants import Calculation, Granularity
from enterprise_data.admin_analytics.data_loaders import (
    fetch_engagement_data,
    fetch_enrollment_data,
    fetch_max_enrollment_datetime,
    fetch_skills_data,
)
from enterprise_data.utils import date_filter, primary_subject_truncate

LOGGER = getLogger(__name__)


class ChartType(Enum):
    """
    Chart types.
    """
    BUBBLE = 'bubble'
    TOP_SKILLS_ENROLLMENT = 'top_skills_enrollment'
    TOP_SKILLS_COMPLETION = 'top_skills_completion'
    COMPLETIONS_OVER_TIME = 'completions_over_time'
    TOP_COURSES_BY_COMPLETIONS = 'top_courses_by_completions'
    TOP_SUBJECTS_BY_COMPLETIONS = 'top_subjects_by_completions'


def fetch_enrollments_cache_expiry_timestamp():
    """Calculate cache expiry timestamp"""
    # TODO: Implement correct cache expiry logic for `enrollments` data.
    #       Current cache expiry logic is based on `enterprise_learner_enrollment` table,
    #       Which has nothing to do with the `enrollments` data. Instead cache expiry should
    #       be based on `fact_enrollment_admin_dash` table. Currently we have no timestamp in
    #       `fact_enrollment_admin_dash` table that can be used for cache expiry. Add a new
    #       column in the table for this purpose and then use that column for cache expiry.
    last_updated_at = fetch_max_enrollment_datetime()
    cache_expiry = (
        last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
    )
    return cache_expiry


def fetch_engagements_cache_expiry_timestamp():
    """Calculate cache expiry timestamp"""
    # TODO: Implement correct cache expiry logic for `engagements` data.
    #       Current cache expiry logic is based on `enterprise_learner_enrollment` table,
    #       Which has nothing to do with the `engagements` data. Instead cache expiry should
    #       be based on `fact_enrollment_engagement_day_admin_dash` table. Currently we have
    #       no timestamp in `fact_enrollment_engagement_day_admin_dash` table that can be used
    #       for cache expiry. Add a new column in the table for this purpose and then use that
    #       column for cache expiry.
    last_updated_at = fetch_max_enrollment_datetime()
    cache_expiry = (
        last_updated_at + timedelta(days=1) if last_updated_at else datetime.now()
    )
    return cache_expiry


def granularity_aggregation(level, group, date, data_frame, aggregation_type="count"):
    """Aggregate data based on granularity"""
    df = data_frame

    period_mapping = {
        Granularity.WEEKLY.value: "W",
        Granularity.MONTHLY.value: "M",
        Granularity.QUARTERLY.value: "Q"
    }

    if level in period_mapping:
        df[date] = df[date].dt.to_period(period_mapping[level]).dt.start_time

    agg_column_name = "count"
    if aggregation_type == "count":
        df = df.groupby(group).size().reset_index()
    elif aggregation_type == "sum":
        df = df.groupby(group).sum().reset_index()
        agg_column_name = "sum"

    df.columns = group + [agg_column_name]
    return df


def calculation_aggregation(calc, data_frame, aggregation_type="count"):
    """Aggregate data based on calculation"""
    df = data_frame

    window_mapping = {
        Calculation.MOVING_AVERAGE_3_PERIOD.value: 3,
        Calculation.MOVING_AVERAGE_7_PERIOD.value: 7,
    }

    aggregation_column = "count" if aggregation_type == "count" else "sum"

    if calc == Calculation.RUNNING_TOTAL.value:
        df[aggregation_column] = df.groupby("enroll_type")[aggregation_column].cumsum()
    elif calc in [Calculation.MOVING_AVERAGE_3_PERIOD.value, Calculation.MOVING_AVERAGE_7_PERIOD.value]:
        df[aggregation_column] = (
            df.groupby("enroll_type")[aggregation_column]
            .rolling(window_mapping[calc])
            .mean()
            .droplevel(level=[0])
        )

    return df


def get_cache_timeout(cache_expiry):
    """
    Helper method to calculate cache timeout in seconds.

    Arguments:
        cache_expiry (datetime): Datetime object denoting the cache expiry.

    Returns:
        (int): Cache timeout in seconds.
    """
    now = datetime.now()
    cache_timeout = 0
    if cache_expiry > now:
        # Calculate cache expiry in seconds from now.
        cache_timeout = (cache_expiry - now).seconds

    return cache_timeout


def fetch_and_cache_enrollments_data(enterprise_id, cache_expiry):
    """
    Helper method to fetch and cache enrollments data.

    Arguments:
        enterprise_id (str): UUID of the enterprise customer in string format.
        cache_expiry (datetime): Datetime object denoting the cache expiry.

    Returns:
        (pandas.DataFrame): The enrollments data.
    """
    cache_key = get_cache_key(
        resource='enterprise-admin-analytics-aggregates-enrollments',
        enterprise_customer=enterprise_id,
    )
    cached_response = TieredCache.get_cached_response(cache_key)

    if cached_response.is_found:
        LOGGER.info(f"Enrollments data found in cache for Enterprise [{enterprise_id}]")
        return cached_response.value
    else:
        enrollments = fetch_enrollment_data(enterprise_id)
        TieredCache.set_all_tiers(
            cache_key, enrollments, get_cache_timeout(cache_expiry)
        )
        return enrollments


def fetch_and_cache_engagements_data(enterprise_id, cache_expiry):
    """
    Helper method to fetch and cache engagements data.

    Arguments:
        enterprise_id (str): UUID of the enterprise customer in string format.
        cache_expiry (datetime): Datetime object denoting the cache expiry.

    Returns:
        (pandas.DataFrame): The engagements data.
    """
    cache_key = get_cache_key(
        resource='enterprise-admin-analytics-aggregates-engagements',
        enterprise_customer=enterprise_id,
    )
    cached_response = TieredCache.get_cached_response(cache_key)

    if cached_response.is_found:
        LOGGER.info(f"Engagements data found in cache for Enterprise [{enterprise_id}]")
        return cached_response.value
    else:
        engagements = fetch_engagement_data(enterprise_id)
        TieredCache.set_all_tiers(
            cache_key, engagements, get_cache_timeout(cache_expiry)
        )
        return engagements


def fetch_and_cache_skills_data(enterprise_id, cache_expiry):
    """
    Helper method to fetch and cache skills data.

    Arguments:
        enterprise_id (str): UUID of the enterprise customer in string format.
        cache_expiry (datetime): Datetime object denoting the cache expiry.

    Returns:
        (pandas.DataFrame): The skills data.
    """
    cache_key = get_cache_key(
        resource='enterprise-admin-analytics-aggregate-skills',
        enterprise_customer=enterprise_id,
    )
    cached_response = TieredCache.get_cached_response(cache_key)

    if cached_response.is_found:
        LOGGER.info(f"Skills data found in cache for Enterprise [{enterprise_id}]")
        return cached_response.value
    else:
        skills = fetch_skills_data(enterprise_id)
        TieredCache.set_all_tiers(
            cache_key, skills, get_cache_timeout(cache_expiry)
        )
        return skills


def get_skills_bubble_chart_df(skills_filtered):
    """ Get the skills data for the bubble chart.

    Args:
        skills_filtered (pandas.DataFrame): The skills data.

    Returns:
        (pandas.DataFrame): The skills data for the bubble chart.
    """

    # Group by skill_name and skill_type, and aggregate enrolls and completions
    skills_aggregated = (
        skills_filtered.groupby(['skill_name', 'skill_type'], as_index=False)
        .agg(enrolls=('enrolls', 'sum'), completions=('completions', 'sum'))
    )

    # Convert enrolls and completions to integers
    skills_aggregated['enrolls'] = skills_aggregated['enrolls'].astype(int)
    skills_aggregated['completions'] = skills_aggregated['completions'].astype(int)

    # Sort the dataframe by enrolls and completions in descending order
    skills_aggregated = skills_aggregated.sort_values(by=['enrolls', 'completions'], ascending=False)

    return skills_aggregated


def get_top_skills_enrollment(skills_filtered):
    """ Get the top skills by enrolls.

    Args:
        skills_filtered (pandas.DataFrame): The skills data.

    Returns:
        (pandas.DataFrame): The top skills by enrolls data
    """

    # Get the top 10 skills by enrolls
    top_skills = (
        skills_filtered.groupby('skill_name')
        .enrolls.sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )

    # Apply primary_subject_truncate to the primary_subject_name column
    skills_filtered['primary_subject_name'] = skills_filtered['primary_subject_name'].apply(primary_subject_truncate)

    # Filter data for the top skills and aggregate enrolls by skill_name and primary_subject_name
    top_skills_enrollment_data = (
        skills_filtered[skills_filtered.skill_name.isin(top_skills)]
        .groupby(['skill_name', 'primary_subject_name'], as_index=False)
        .agg(count=('enrolls', 'sum'))
    )

    # Sort the dataframe by primary_subject_name
    top_skills_enrollment_data = top_skills_enrollment_data.sort_values(by="primary_subject_name")

    return top_skills_enrollment_data


def get_top_skills_completion(skills_filtered):
    """ Get the top skills by completions.

    Args:
        skills_filtered (pandas.DataFrame): The skills data.

    Returns:
        (pandas.DataFrame): The top skills by completions
    """

    # Get the top 10 skills by completions
    top_skills = (
        skills_filtered.groupby('skill_name')
        .completions.sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )

    # Apply primary_subject_truncate to the primary_subject_name column
    skills_filtered['primary_subject_name'] = skills_filtered['primary_subject_name'].apply(primary_subject_truncate)

    # Filter data for the top skills and aggregate completions by skill_name and primary_subject_name
    top_skills_completion_data = (
        skills_filtered[skills_filtered.skill_name.isin(top_skills)]
        .groupby(['skill_name', 'primary_subject_name'], as_index=False)
        .agg(count=('completions', 'sum'))
    )

    # Sort the dataframe by primary_subject_name
    top_skills_completion_data = top_skills_completion_data.sort_values(by='primary_subject_name')

    return top_skills_completion_data


def get_skills_chart_data(chart_type, start_date, end_date, skills):
    """
    Get chart data for skill charts.

    Arguments:
        chart_type (ChartType): The type of chart to generate.
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        skills (pandas.DataFrame): The skills data.
    """
    skills_filtered = date_filter(start=start_date, end=end_date, data_frame=skills.copy(), date_column='date')
    if chart_type == ChartType.BUBBLE:
        return get_skills_bubble_chart_df(skills_filtered=skills_filtered.copy())
    elif chart_type == ChartType.TOP_SKILLS_ENROLLMENT:
        return get_top_skills_enrollment(skills_filtered=skills_filtered.copy())
    elif chart_type == ChartType.TOP_SKILLS_COMPLETION:
        return get_top_skills_completion(skills_filtered=skills_filtered.copy())
    else:
        raise ValueError(f"Invalid chart type: {chart_type}")


def get_top_skills_csv_data(skills, start_date, end_date):
    """ Get the top skills data for CSV download.

    Args:
        skills (pandas.DataFrame): The skills data.
        start_date (str): The start date for the date filter.
        end_date (str): The end date for the date filter.

    Returns:
        (pandas.DataFrame): The top skills data for CSV download.
    """
    dff = get_skills_chart_data(
        chart_type=ChartType.BUBBLE,
        start_date=start_date,
        end_date=end_date,
        skills=skills.copy(),
    )
    dff = dff.sort_values(by='enrolls', ascending=False)
    return dff
