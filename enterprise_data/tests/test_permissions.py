"""
Tests for permissions
"""

from logging import getLogger

from mock import MagicMock, patch
from pytest import mark

from django.test import TestCase

from enterprise_data.permissions import HasDataAPIDjangoGroupAccess, IsStaffOrEnterpriseUser
from test_utils import UserFactory

LOGGER = getLogger(__name__)


class PermissionsTestCase(TestCase):
    """
    Common logic for permissions class tests.
    """
    def setUp(self):
        super(PermissionsTestCase, self).setUp()
        self.enterprise_id = 'fake-enterprise-id'
        self.user = UserFactory()
        self.request = MagicMock(
            user=self.user,
            parser_context={
                'kwargs': {
                    'enterprise_id': self.enterprise_id
                }
            },
            session={},
            auth=MagicMock()
        )

        enterprise_api_client = patch('enterprise_data.permissions.EnterpriseApiClient')
        self.enterprise_api_client = enterprise_api_client.start()
        self.addCleanup(enterprise_api_client.stop)


@mark.django_db
class TestIsStaffOrEnterpriseUser(PermissionsTestCase):
    """
    Tests of the IsStaffOrEnterpriseUser permission
    """

    def setUp(self):
        super(TestIsStaffOrEnterpriseUser, self).setUp()
        self.permission = IsStaffOrEnterpriseUser()

    def test_staff_access(self):
        self.user.is_staff = True
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_enterprise_learner_has_access(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {
            'enterprise_customer': {
                'uuid': self.enterprise_id
            },
            'groups': ['enterprise_data_api_access'],
        }
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_wrong_enterprise_learner_has_no_access(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {
            'enterprise_customer': {
                'uuid': 'some-other-enterprise-id'
            },
            'groups': ['enterprise_data_api_access'],
        }
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_enterprise_learner_has_no_group_access(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {
            'enterprise_customer': {
                'uuid': 'some-other-enterprise-id'
            },
            'groups': [],
        }
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_no_enterprise_learner_for_user(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {}
        self.assertFalse(self.permission.has_permission(self.request, None))


@mark.django_db
class TestHasDataAPIDjangoGroupAccess(PermissionsTestCase):
    """
    Tests of the IsStaffOrEnterpriseUser permission
    """

    def setUp(self):
        super(TestHasDataAPIDjangoGroupAccess, self).setUp()
        self.permission = HasDataAPIDjangoGroupAccess()

    def test_staff_access_without_group_permission(self):
        self.user.is_staff = True
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {}
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_staff_access_with_group_permission(self):
        self.user.is_staff = True
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': self.enterprise_id
        }
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_enterprise_user_has_access_with_group_permission(self):
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': self.enterprise_id
        }
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_enterprise_user_without_group_permission(self):
        self.enterprise_api_client.return_value.get_with_access_to.return_value = {}
        self.assertFalse(self.permission.has_permission(self.request, None))
