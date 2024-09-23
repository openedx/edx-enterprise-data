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
)

LOGGER = getLogger(__name__)


class ChartType(Enum):
    """
    Chart types.
    """
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
