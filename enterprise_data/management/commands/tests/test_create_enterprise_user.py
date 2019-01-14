"""
Tests for create_enterprise_user management command
"""
from __future__ import absolute_import, unicode_literals

from unittest import TestCase

from mock import mock
from pytest import mark

from django.core.management import call_command

from enterprise_data.models import EnterpriseUser
from enterprise_data.tests.test_utils import EnterpriseUserFactory


@mark.django_db
class TestCreateEnterpriseUserCommand(TestCase):
    """ test class here """

    def setUp(self):
        super(TestCreateEnterpriseUserCommand, self).setUp()
        self.uuid = 'a'*32

    def test_create_enterpriseuser(self):
        """
        Manangement command should successfully be able to create EnterpriseUser
        """
        assert EnterpriseUser.objects.count() == 0

        args = [self.uuid]
        call_command('create_enterprise_user', *args)

        assert EnterpriseUser.objects.count() == 1
        assert EnterpriseUser.objects.filter(enterprise_id=args[0]).count() == 1

    def test_create_enterpriseuser_error(self):
        """
        Manangement command should successfully be able to create EnterpriseUser
        """
        EnterpriseUserFactory(enterprise_id=self.uuid)
        assert EnterpriseUser.objects.count() == 1

        args = [self.uuid]
        with mock.patch('enterprise_data.tests.test_utils.EnterpriseUserFactory') as mock_factory:
            mock_factory.side_effect = [Exception]
            with self.assertRaises(Exception):
                call_command('create_enterprise_user', *args)

        assert EnterpriseUser.objects.count() == 1
