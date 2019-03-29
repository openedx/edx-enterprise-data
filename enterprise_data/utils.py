# -*- coding: utf-8 -*-
"""
Utility functions for Enterprise Data app.
"""
from __future__ import absolute_import, unicode_literals

import hashlib

import six


def update_session_with_enterprise_data(request, enterprise_id, **kwargs):
    """
    DRY method to set provided parameters on the request session.

    Set provided parameters against the provided enterprise id.

    The values will be set in session in the following format:
    {
        'enterprises_with_access': {'ee5e6b3a-069a-4947-bb8d-d2dbc323396c': True},
        'enable_audit_enrollment': {'ee5e6b3a-069a-4947-bb8d-d2dbc323396c': False}
    }

    Arguments:
        request: Http request
        enterprise_id: UUID of enterprise
        **kwargs: Keyword arguments that need to be present in request session

    """
    for item, value in six.iteritems(kwargs):
        session_key_data = request.session.get(item, {})
        session_key_data.update({str(enterprise_id): value})
        request.session.update({
            item: session_key_data
        })


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
    key = '__'.join(['{}:{}'.format(item, value) for item, value in six.iteritems(kwargs)])

    return hashlib.md5(key.encode('utf-8')).hexdigest()
