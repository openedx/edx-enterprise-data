"""
Tests for the `enterprise-data` models module.
"""


import unittest

import ddt
from pytest import mark

from enterprise_data_roles.tests import factories


@mark.django_db
@ddt.ddt
class TestEnterpriseDataFeatureRole(unittest.TestCase):
    """
    Tests for Enterprise Data Feature Role model
    """

    def setUp(self):
        self.enterprise_data_feature_role = factories.EnterpriseDataFeatureRoleFactory(name="Test Role")
        self.enterprise_data_role_assignment = factories.EnterpriseDataRoleAssignmentFactory()

        super().setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = "EnterpriseDataFeatureRole(name=Test Role)"
        assert expected_str == method(self.enterprise_data_feature_role)


@mark.django_db
@ddt.ddt
class TestEnterpriseDataRoleAssignment(unittest.TestCase):
    """
    Tests for Enterprise Data Role Assignment model
    """

    def setUp(self):
        self.enterprise_data_role_assignment = factories.EnterpriseDataRoleAssignmentFactory(
            role__name="Test Role",
            user__id=1,
        )

        super().setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = "EnterpriseDataRoleAssignment(name=Test Role, user=1)"
        assert expected_str == method(self.enterprise_data_role_assignment)
