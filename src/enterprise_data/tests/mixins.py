"""
Mixins for enterprise data tests.
"""


from edx_rest_framework_extensions.auth.jwt.cookies import jwt_cookie_name
from edx_rest_framework_extensions.auth.jwt.tests.utils import generate_jwt_token, generate_unversioned_payload


class JWTTestMixin:
    """
    Mixin for JWT test related utils.
    """

    def set_jwt_cookie(self, system_wide_role='enterprise_admin', context='some_context'):
        """
        Set jwt token in cookies
        """
        role_data = f'{system_wide_role}'
        if context is not None:
            role_data += f':{context}'

        payload = generate_unversioned_payload(self.user)
        payload.update({
            'roles': [role_data]
        })
        jwt_token = generate_jwt_token(payload)

        self.client.cookies[jwt_cookie_name()] = jwt_token
