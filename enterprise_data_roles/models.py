# -*- coding: utf-8 -*-
"""
Database models for enterprise data.
"""
from __future__ import absolute_import, unicode_literals

from edx_rbac.models import UserRole, UserRoleAssignment

from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class EnterpriseDataFeatureRole(UserRole):
    """
    User role definitions specific to EnterpriseData.

     .. no_pii:
    """

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return "EnterpriseDataFeatureRole(name={name})".format(name=self.name)

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


@python_2_unicode_compatible
class EnterpriseDataRoleAssignment(UserRoleAssignment):
    """
    Model to map users to a EnterpriseDataFeatureRole.

     .. no_pii:
    """

    role_class = EnterpriseDataFeatureRole

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return "EnterpriseDataRoleAssignment(name={name}, user={user})".format(
            name=self.role.name,
            user=self.user.id,
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()
