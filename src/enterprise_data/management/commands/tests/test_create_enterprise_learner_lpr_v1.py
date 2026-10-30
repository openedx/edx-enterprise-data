"""
Tests for create_enterprise_learner_lpr_v1 management command
"""
from unittest import TestCase, mock

from pytest import mark

from django.core.management import call_command

from enterprise_data.models import EnterpriseLearner
from enterprise_data.tests.test_utils import EnterpriseLearnerFactory


@mark.django_db
class TestCreateEnterpriseLearnerCommand(TestCase):
    """
    Tests to validate the behavior of `./manage.py create_enterprise_learner_lpr_v1` management command.
    """

    def setUp(self):
        super().setUp()
        self.uuid = 'a'*32

    def test_create_enterprise_learner(self):
        """
        Management command should successfully be able to create EnterpriseLearner
        """
        assert EnterpriseLearner.objects.count() == 0

        args = [self.uuid]
        call_command('create_enterprise_learner_lpr_v1', *args)

        assert EnterpriseLearner.objects.count() == 1
        assert EnterpriseLearner.objects.filter(enterprise_customer_uuid=args[0]).count() == 1

    def test_create_enterprise_learner_error(self):
        """
        Management command should handle exceptions gracefully.
        """
        EnterpriseLearnerFactory(enterprise_customer_uuid=self.uuid)
        assert EnterpriseLearner.objects.count() == 1

        args = [self.uuid]
        with mock.patch('enterprise_data.tests.test_utils.EnterpriseLearnerFactory') as mock_factory:
            mock_factory.side_effect = [Exception]
            with self.assertRaises(Exception):
                call_command('create_enterprise_learner_lpr_v1', *args)

        assert EnterpriseLearner.objects.count() == 1
