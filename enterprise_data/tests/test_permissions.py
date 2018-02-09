"""
Tests for permissions
"""

from logging import getLogger

from mock import MagicMock, patch
from pytest import mark, raises
from rest_framework.test import APIClient

from django.test import RequestFactory, TestCase

from enterprise_data.permissions import IsStaffOrEnterpriseUser
from test_utils import UserFactory

LOGGER = getLogger(__name__)


@mark.django_db
class TestIsStaffOrEnterpriseUser(TestCase):
    """
    Tests of the IsStaffOrEnterpriseUser permission
    """

    def setUp(self):
        super(TestIsStaffOrEnterpriseUser, self).setUp()
        self.permission = IsStaffOrEnterpriseUser()
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

    def test_staff_access(self):
        self.user.is_staff = True
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_enterprise_learner_has_access(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {
            'enterprise_customer': {
                'uuid': self.enterprise_id
            }
        }
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_wrong_enterprise_learner_has_no_access(self):
        self.enterprise_api_client.return_value.get_enterprise_learner.return_value = {
            'enterprise_customer': {
                'uuid': 'some-other-enterprise-id'
            }
        }
        self.assertFalse(self.permission.has_permission(self.request, None))
