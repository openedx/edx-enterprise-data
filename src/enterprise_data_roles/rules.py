"""
Rules needed to restrict access to the enterprise data api.
"""


import crum
import rules
from edx_rbac.utils import request_user_has_implicit_access_via_jwt, user_has_access_via_database
from edx_rest_framework_extensions.auth.jwt.authentication import get_decoded_jwt_from_auth
from edx_rest_framework_extensions.auth.jwt.cookies import get_decoded_jwt

from django.urls import resolve

from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataRoleAssignment


@rules.predicate
def request_user_has_implicit_access(*args, **kwargs):
    """
    Check that if request user has implicit access to `ENTERPRISE_DATA_ADMIN_ROLE` feature role.

    Returns:
        boolean: whether the request user has access or not
    """
    request = crum.get_current_request()
    _, _, request_kwargs = resolve(request.path)
    enterprise_id_in_request = request_kwargs.get('enterprise_id')

    decoded_jwt = get_decoded_jwt(request) or get_decoded_jwt_from_auth(request)
    return request_user_has_implicit_access_via_jwt(
        decoded_jwt,
        ENTERPRISE_DATA_ADMIN_ROLE,
        enterprise_id_in_request
    )


@rules.predicate
def request_user_has_explicit_access(*args, **kwargs):
    """
    Check that if request user has explicit access to `ENTERPRISE_DATA_ADMIN_ROLE` feature role.

    Returns:
        boolean: whether the request user has access or not
    """
    request = crum.get_current_request()
    _, _, request_kwargs = resolve(request.path)
    enterprise_id_in_request = request_kwargs.get('enterprise_id')

    return user_has_access_via_database(
        request.user,
        ENTERPRISE_DATA_ADMIN_ROLE,
        EnterpriseDataRoleAssignment,
        enterprise_id_in_request
    )


rules.add_perm(
    'can_access_enterprise',
    request_user_has_implicit_access | request_user_has_explicit_access
)
