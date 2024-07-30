"""
Utility functions for fetching data from the database.
"""
from datetime import datetime

from edx_django_utils.cache import TieredCache, get_cache_key

from enterprise_data.admin_analytics.data_loaders import fetch_engagement_data, fetch_enrollment_data


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
        return cached_response.value
    else:
        engagements = fetch_engagement_data(enterprise_id)
        TieredCache.set_all_tiers(
            cache_key, engagements, get_cache_timeout(cache_expiry)
        )
        return engagements
