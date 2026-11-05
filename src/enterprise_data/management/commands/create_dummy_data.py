"""
management command for creating enterprise enrollments in bulk
"""

from django.core.management.base import BaseCommand, CommandError

from enterprise_data.tests.test_utils import EnterpriseEnrollmentFactory, EnterpriseUserFactory


class Command(BaseCommand):
    """ management command class for creating enterprise enrollments in bulk """
    help = 'Creates 10 enterprise users with 5 random enrollments each'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_id',
            type=str,
            help='UUID for an enterprise'
        )

    def handle(self, *args, **options):
        enterprise_id = options['enterprise_id']
        try:
            for _ in range(10):
                user = EnterpriseUserFactory(enterprise_id=enterprise_id)
                for _ in range(5):
                    EnterpriseEnrollmentFactory(
                        enterprise_id=enterprise_id,
                        enterprise_user=user,
                        user_email=user.user_email)
        except Exception as exc:
            info = (
                'Error trying to create Enrollments for enterprise '
                '{}: {}'.format(enterprise_id, exc)
            )
            raise CommandError(info) from exc
