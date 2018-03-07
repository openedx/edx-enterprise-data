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

    def get_user_enterprise_id(self, auth_token, user):
        """
        Get the enterprise learner model from the LMS for the given user.

        Returns: learner or None if unable to get or user is not associated with an enterprise
        """
        enterprise_client = EnterpriseApiClient(auth_token)
        enterprise_learner_data = enterprise_client.get_enterprise_learner(user)
        if not enterprise_learner_data:
            return None

        return enterprise_learner_data['enterprise_customer']['uuid']

    def has_permission(self, request, view):
        """
        Verify the user is staff or the associated enterprise matches the requested enterprise.
        """
        if request.user.is_staff:
            return True

        if not hasattr(request.session, 'enterprise_id'):
            request.session['enterprise_id'] = self.get_user_enterprise_id(request.auth, request.user)

        enterprise_in_url = request.parser_context.get('kwargs', {}).get('enterprise_id', '')

        permitted = request.session['enterprise_id'] == enterprise_in_url
        if not permitted:
            LOGGER.warning('User {} denied access to EnterpriseEnrollments for enterprise {}'
                           .format(request.user, enterprise_in_url))

        return permitted
