"""
management command for creating enterprise enrollments in bulk
"""

from random import choice

from django.core.management.base import BaseCommand, CommandError

from enterprise_data.tests.test_utils import EnterpriseLearnerEnrollmentFactory, EnterpriseLearnerFactory


class Command(BaseCommand):
    """
    management command class for creating enterprise enrollments in bulk for learner progress report (LPR) v1
    """
    help = 'Creates 10 enterprise learners with 5 random enterprise learner enrollments each with random consent grants'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_customer_uuid',
            type=str,
            help='UUID for an enterprise'
        )

    def handle(self, *args, **options):
        enterprise_customer_uuid = options['enterprise_customer_uuid']
        try:
            for _ in range(10):
                ent_user = EnterpriseLearnerFactory(
                    enterprise_customer_uuid=enterprise_customer_uuid
                )
                for _ in range(5):
                    EnterpriseLearnerEnrollmentFactory(
                        enterprise_customer_uuid=enterprise_customer_uuid,
                        enterprise_user_id=ent_user.enterprise_user_id,
                        is_consent_granted=choice([True, False]),
                    )
        except Exception as exc:
            info = (
                'Error trying to create Enrollments for enterprise '
                '{}: {}'.format(enterprise_customer_uuid, exc)
            )
            raise CommandError(info) from exc
