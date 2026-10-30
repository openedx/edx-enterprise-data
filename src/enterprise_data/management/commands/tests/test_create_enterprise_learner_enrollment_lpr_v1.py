"""
Tests for create_enterprise_learner_enrollment_lpr_v1 management command
"""
from unittest import TestCase, mock

from pytest import mark

from django.core.management import call_command

from enterprise_data.models import EnterpriseLearner, EnterpriseLearnerEnrollment
from enterprise_data.tests.test_utils import EnterpriseLearnerFactory


@mark.django_db
class TestCreateEnterpriseLearnerEnrollmentCommand(TestCase):
    """ Tests for create_enterprise_learner_enrollment_lpr_v1 management command"""

    def setUp(self):
        super().setUp()
        self.uuid = 'a'*32
        self.enterprise_user = EnterpriseLearnerFactory(enterprise_customer_uuid=self.uuid)

    def test_create_enterprise_learner_enrollment_lpr_v1_with_dsc_disabled(self):
        """
        Management command should successfully be able to create EnterpriseLearnerEnrollment with DSC Disabled
        """
        assert EnterpriseLearner.objects.count() == 1
        assert EnterpriseLearnerEnrollment.objects.count() == 0

        args = [self.uuid, self.enterprise_user.enterprise_user_id]
        call_command('create_enterprise_learner_enrollment_lpr_v1', *args)

        assert EnterpriseLearnerEnrollment.objects.count() == 1
        enterprise_learner_enrollment = EnterpriseLearnerEnrollment.objects.filter(
            enterprise_customer_uuid=args[0]
        )
        assert enterprise_learner_enrollment.count() == 1
        assert enterprise_learner_enrollment[0].progress_status is None
        assert enterprise_learner_enrollment[0].letter_grade is None
        assert enterprise_learner_enrollment[0].enterprise_user_id is None
        assert enterprise_learner_enrollment[0].user_username is None
        assert enterprise_learner_enrollment[0].user_first_name is None
        assert enterprise_learner_enrollment[0].user_last_name is None
        assert enterprise_learner_enrollment[0].user_email is None
        assert enterprise_learner_enrollment[0].enterprise_user is None

    def test_create_enterprise_learner_enrollment_lpr_v1_with_dsc_enabled(self):
        """
        Management command should successfully be able to create EnterpriseLearnerEnrollment with DSC enabled
        """
        assert EnterpriseLearner.objects.count() == 1
        assert EnterpriseLearnerEnrollment.objects.count() == 0

        args = [self.uuid, self.enterprise_user.enterprise_user_id, '--consent_granted']
        call_command('create_enterprise_learner_enrollment_lpr_v1', *args)

        assert EnterpriseLearnerEnrollment.objects.count() == 1
        enterprise_learner_enrollment = EnterpriseLearnerEnrollment.objects.filter(
            enterprise_customer_uuid=args[0]
        )
        assert enterprise_learner_enrollment.count() == 1
        assert enterprise_learner_enrollment[0].letter_grade is not None
        assert enterprise_learner_enrollment[0].last_activity_date is not None
        assert enterprise_learner_enrollment[0].progress_status is not None
        assert enterprise_learner_enrollment[0].enterprise_user_id is not None
        assert enterprise_learner_enrollment[0].user_username is not None
        assert enterprise_learner_enrollment[0].user_first_name is not None
        assert enterprise_learner_enrollment[0].user_last_name is not None
        assert enterprise_learner_enrollment[0].enterprise_user is not None
        assert enterprise_learner_enrollment[0].user_email is not None
        assert EnterpriseLearner.objects.count() == 1

    def test_create_enterprise_learner_enrollment_lpr_v1_error(self):
        """
        Management command will not create enrollment if an error is thrown
        """
        assert EnterpriseLearnerEnrollment.objects.count() == 0

        args = [self.uuid, self.enterprise_user.enterprise_user_id]
        with mock.patch('enterprise_data.tests.test_utils.EnterpriseLearnerEnrollmentFactory') as mock_factory:
            mock_factory.side_effect = [Exception]
            with self.assertRaises(Exception):
                call_command('create_enterprise_learner_enrollment_lpr_v1', *args)

        assert EnterpriseLearnerEnrollment.objects.count() == 0
