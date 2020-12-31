"""
Database models for enterprise data.
"""


from edx_rbac.models import UserRole, UserRoleAssignment

from django.db import models


class EnterpriseDataFeatureRole(UserRole):
    """
    User role definitions specific to EnterpriseData.

     .. no_pii:
    """

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return f"EnterpriseDataFeatureRole(name={self.name})"

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseDataRoleAssignment(UserRoleAssignment):
    """
    Model to map users to a EnterpriseDataFeatureRole.

     .. no_pii:
    """

    role_class = EnterpriseDataFeatureRole
    enterprise_id = models.UUIDField(blank=True, null=True, verbose_name='Enterprise Customer UUID')

    def get_context(self):
        """
        Return the enterprise customer id or `*` if the user has access to all resources.
        """
        enterprise_id = '*'
        if self.enterprise_id:
            # converting the UUID('ee5e6b3a-069a-4947-bb8d-d2dbc323396c') to 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
            enterprise_id = str(self.enterprise_id)

        return enterprise_id

    def __str__(self):
        """
        Return human-readable string representation.
        """
        return "EnterpriseDataRoleAssignment(name={name}, user={user})".format(
            name=self.role.name,  # pylint: disable=no-member
            user=self.user.id,
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()
