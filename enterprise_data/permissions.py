"""
Permissions needed to restrict access to the enterprise data api.
"""
from __future__ import absolute_import, unicode_literals

from logging import getLogger

from rest_framework import permissions

from enterprise_data.clients import EnterpriseApiClient

LOGGER = getLogger(__name__)


class IsStaffOrEnterpriseUser(permissions.BasePermission):
    """
    Permission that checks to see if the request user is staff or is associated with the enterprise in the request.

    NOTE: This permission check may make a request to the LMS to get the enterprise association if it is not already in
    the session. This fetch should go away when JWT Scopes are fully implemented and the association is stored on
    the token.
    """

    ENTERPRISE_DATA_API_GROUP = 'enterprise_data_api_access'

    def get_user_enterprise_data(self, auth_token, user):
        """
        Get the enterprise learner model from the LMS for the given user.

        Returns: learner or None if unable to get or user is not associated with an enterprise
        """
        enterprise_client = EnterpriseApiClient(auth_token)
        enterprise_learner_data = enterprise_client.get_enterprise_learner(user)
        if not enterprise_learner_data:
            return None

        return {
            'enterprise_id': enterprise_learner_data['enterprise_customer']['uuid'],
            'enterprise_groups': enterprise_learner_data['groups'],
        }

    def has_permission(self, request, view):
        """
        Verify the user is staff or the associated enterprise matches the requested enterprise.
        """
        if request.user.is_staff:
            return True

        if not hasattr(request.session, 'enterprise_id') or not hasattr(request.session, 'enterprise_groups'):
            enterprise_data = self.get_user_enterprise_data(request.auth, request.user)
            if not enterprise_data:
                return False
            request.session['enterprise_id'] = enterprise_data['enterprise_id']
            request.session['enterprise_groups'] = enterprise_data['enterprise_groups']

        enterprise_in_url = request.parser_context.get('kwargs', {}).get('enterprise_id', '')

        permitted = (
            request.session['enterprise_id'] == enterprise_in_url and
            self.ENTERPRISE_DATA_API_GROUP in request.session['enterprise_groups']
        )
        if not permitted:
            LOGGER.warning('User {} denied access to EnterpriseEnrollments for enterprise {}'
                           .format(request.user, enterprise_in_url))

        return permitted


class HasDataAPIDjangoGroupAccess(permissions.BasePermission):
    """
    Permission that checks to see if the request user is part of the enterprise_data_api django group.

    Also checks that the user is authorized for the request's enterprise.
    """

    def get_enterprise_with_access_to(self, auth_token, user, enterprise_id):
        """
        Get the enterprise customer data that the user has enterprise_data_api access to.

        Returns: enterprise or None if unable to get or user is not associated with an enterprise
        """
        enterprise_client = EnterpriseApiClient(auth_token)
        enterprise_data = enterprise_client.get_with_access_to(user, enterprise_id)
        if not enterprise_data:
            return None

        return enterprise_data

    def has_permission(self, request, view):
        """
        Verify the user is staff or the associated enterprise matches the requested enterprise.
        """
        enterprise_in_url = request.parser_context.get('kwargs', {}).get('enterprise_id', '')

        if ('enterprises_with_access' not in request.session or
                enterprise_in_url not in request.session['enterprises_with_access']):
            request.session['enterprises_with_access'] = {}
            enterprise_data = self.get_enterprise_with_access_to(request.auth, request.user, enterprise_in_url)
            if not enterprise_data:
                request.session['enterprises_with_access'][enterprise_in_url] = False
            else:
                request.session['enterprises_with_access'][enterprise_in_url] = True

        permitted = request.session['enterprises_with_access'][enterprise_in_url]
        if not permitted:
            LOGGER.warning('User {} denied access to EnterpriseEnrollments for enterprise {}'
                           .format(request.user, enterprise_in_url))

        return permitted
