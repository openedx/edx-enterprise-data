"""
Tests for create_enterprise_enrollment management command
"""
from unittest import TestCase, mock

from pytest import mark

from django.core.management import call_command

from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser
from enterprise_data.tests.test_utils import EnterpriseUserFactory


@mark.django_db
class TestCreateEnterpriseEnrollmentCommand(TestCase):
    """ test class here """

    def setUp(self):
        super().setUp()
        self.uuid = 'a'*32
        self.enterprise_user = EnterpriseUserFactory(enterprise_id=self.uuid)

    def test_create_enterpriseenrollment(self):
        """
        Manangement command should successfully be able to create EnterpriseEnrollment
        """
        assert EnterpriseUser.objects.count() == 1
        assert EnterpriseEnrollment.objects.count() == 0

        args = [self.uuid, self.enterprise_user.enterprise_user_id]
        call_command('create_enterprise_enrollment', *args)

        assert EnterpriseEnrollment.objects.count() == 1
        assert EnterpriseEnrollment.objects.filter(
            enterprise_id=args[0]
        ).count() == 1

    def test_create_enterpriseenrollment_error(self):
        """
        Management command will not create enrollment if an error is thrown
        """
        assert EnterpriseEnrollment.objects.count() == 0

        args = [self.uuid, self.enterprise_user.enterprise_user_id]
        with mock.patch('enterprise_data.tests.test_utils.EnterpriseEnrollmentFactory') as mock_factory:
            mock_factory.side_effect = [Exception]
            with self.assertRaises(Exception):
                call_command('create_enterprise_enrollment', *args)

        assert EnterpriseEnrollment.objects.count() == 0
