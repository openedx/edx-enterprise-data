"""
Utility functions for Enterprise Data app.
"""
import hashlib
import random
import time
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from logging import getLogger

LOGGER = getLogger(__name__)


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...

    Example:
        >>> get_cache_key(site_domain="example.com", resource="enterprise_customer_users")
        # Here is key format for above call
        # "site_domain:example.com__resource:enterprise_customer_users"
        a54349175618ff1659dee0978e3149ca

    Arguments:
        **kwargs: Keyword arguments that need to be present in cache key.

    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join([f'{item}:{value}' for item, value in kwargs.items()])

    return hashlib.md5(key.encode('utf-8')).hexdigest()


def get_unique_id():
    """
    Return a unique 32 bit integer.
    """
    return random.getrandbits(32)


def subtract_one_month(original_date):
    """
    Return a date exactly one month prior to the passed in date.
    """
    one_day = timedelta(days=1)
    one_month_earlier = original_date - one_day
    while one_month_earlier.month == original_date.month or one_month_earlier.day > original_date.day:
        one_month_earlier -= one_day
    return one_month_earlier


def timeit(func):
    """
    Measure time taken by a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        LOGGER.info(f'Time taken by {func.__name__}: {end - start} seconds')
        return result

    return wrapper


@contextmanager
def timer(prefix):
    """
    Context manager to measure the time taken by a block of code.

    Arguments:
        prefix (str): The prefix to print in the log.
    """
    start = time.time()
    yield
    difference = time.time() - start
    LOGGER.info(f"TIMER:: {prefix} took {difference:.20f} seconds")


def date_filter(start, end, data_frame, date_column):
    """
    Filter a pandas DataFrame by date range.

    Arguments:
        start (DatetimeScalar | NaTType | None): The start date.
        end (DatetimeScalar | NaTType | None): The end date.
        data_frame (pandas.DataFrame): The DataFrame to filter.
        date_column (str): The name of the date column.

    Returns:
        (pandas.DataFrame): The filtered DataFrame.
    """
    return data_frame[(start <= data_frame[date_column]) & (data_frame[date_column] <= end)]


def primary_subject_truncate(x):
    """
    Truncate primary subject to a few categories.
    """
    if x in [
        "business-management",
        "computer-science",
        "data-analysis-statistics",
        "engineering",
        "communication",
    ]:
        return x
    else:
        return "other"
