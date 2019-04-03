"""
Rules needed to restrict access to the enterprise data api.
"""
from __future__ import absolute_import, unicode_literals

import rules
from edx_rbac.utils import (
    get_decoded_jwt_from_request,
    get_request_or_stub,
    request_user_has_implicit_access_via_jwt,
    user_has_access_via_database,
)

from django.urls import resolve

from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE, SYSTEM_ENTERPRISE_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataRoleAssignment


def has_correct_context_for_implicit_access(request, decoded_jwt, system_wide_role_name):
    """
    Check if request has correct role assignement context.
    """
    __, __, kwargs = resolve(request.path)
    enterprise_id_in_request = kwargs.get('enterprise_id')

    jwt_roles_claim = decoded_jwt.get('roles', [])

    for role_data in jwt_roles_claim:
        role_in_jwt, enterprise_id_in_jwt = role_data.split(':')
        if role_in_jwt == system_wide_role_name:
            return enterprise_id_in_jwt == enterprise_id_in_request

    return False


def has_correct_context_for_explicit_access(request):
    """
    Check if request has correct role assignement context.
    """
    __, __, kwargs = resolve(request.path)
    enterprise_id_in_request = kwargs.get('enterprise_id')

    try:
        role_assignment = EnterpriseDataRoleAssignment.objects.get(
            user=request.user,
            role__name=ENTERPRISE_DATA_ADMIN_ROLE
        )
    except EnterpriseDataRoleAssignment.DoesNotExist:
        return False

    # if there is no enterprise_id set than user is allowed
    if role_assignment.get_context() is None:
        return True

    return role_assignment.get_context() == enterprise_id_in_request


@rules.predicate
def request_user_has_implicit_access(*args, **kwargs):  # pylint: disable=unused-argument
    """
    Check that if request user has implicit access to `ENTERPRISE_DATA_ADMIN_ROLE` feature role.

    Returns:
        boolean: whether the request user has access or not
    """
    request = get_request_or_stub()

    decoded_jwt = get_decoded_jwt_from_request(request)
    implicit_access = request_user_has_implicit_access_via_jwt(decoded_jwt, ENTERPRISE_DATA_ADMIN_ROLE)

    if not implicit_access:
        return False

    return has_correct_context_for_implicit_access(request, decoded_jwt, SYSTEM_ENTERPRISE_ADMIN_ROLE)


@rules.predicate
def request_user_has_explicit_access(*args, **kwargs):  # pylint: disable=unused-argument
    """
    Check that if request user has explicit access to `ENTERPRISE_DATA_ADMIN_ROLE` feature role.

    Returns:
        boolean: whether the request user has access or not
    """
    request = get_request_or_stub()

    explicit_access = user_has_access_via_database(
        request.user,
        ENTERPRISE_DATA_ADMIN_ROLE,
        EnterpriseDataRoleAssignment
    )

    if not explicit_access:
        return False

    return has_correct_context_for_explicit_access(request)


rules.add_perm('can_access_enterprise', request_user_has_implicit_access | request_user_has_explicit_access)
