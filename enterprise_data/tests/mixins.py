# -*- coding: utf-8 -*-
"""
Mixins for enterprise data tests.
"""
from __future__ import absolute_import, unicode_literals

from edx_rest_framework_extensions.auth.jwt.cookies import jwt_cookie_name
from edx_rest_framework_extensions.auth.jwt.tests.utils import generate_jwt_token, generate_unversioned_payload


class JWTTestMixin(object):
    """
    Mixin for JWT test related utils.
    """

    def set_jwt_cookie(self, system_wide_role='enterprise_admin', context='some_context'):
        """
        Set jwt token in cookies
        """
        role_data = '{system_wide_role}'.format(system_wide_role=system_wide_role)
        if context is not None:
            role_data += ':{context}'.format(context=context)

        payload = generate_unversioned_payload(self.user)
        payload.update({
            'roles': [role_data]
        })
        jwt_token = generate_jwt_token(payload)

        self.client.cookies[jwt_cookie_name()] = jwt_token
