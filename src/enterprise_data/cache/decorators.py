"""
Decorators for caching the result of a function.
"""
from functools import wraps
from logging import getLogger

from enterprise_data import cache

LOGGER = getLogger(__name__)


def cache_it(timeout=cache.DEFAULT_TIMEOUT):
    """
    Function to return the decorator to cache the result of a method.

    Note: This decorator will only work for class methods.

    Arguments:
        timeout (int): Cache timeout in seconds.

    Returns:
        (function): Decorator function.
    """

    def inner_decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            """
            Wrapper function to cache the result of the function.
            """
            cache_key = cache.get_key(func.__name__, *args, **kwargs)
            cached_response = cache.get(cache_key)
            if cached_response.is_found:
                LOGGER.info("[ANALYTICS]: Cache hit for key: (%s)", (func.__name__, args, kwargs))
                return cached_response.value

            LOGGER.info("[ANALYTICS]: Cache miss for key: (%s)", (func.__name__, args, kwargs))
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return inner_decorator
