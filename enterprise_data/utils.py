"""
Utility functions for Enterprise Data app.
"""


import hashlib


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
