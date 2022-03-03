"""
Management command for creating enterprise learner enrollments
"""


import sys

from django.core.management.base import BaseCommand, CommandError

import enterprise_data.tests.test_utils


class Command(BaseCommand):
    """ Management command for creating dummy `EnterpriseLearnerEnrollment` instances for (LPR) V1."""

    help = 'Creates an EnterpriseLearnerEnrollment with randomized attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_customer_uuid',
            type=str,
            help='UUID for an enterprise'
        )
        parser.add_argument(
            'enterprise_user_id',
            type=int,
            default=None,
            help='enterprise_user_id for an enterprise_user'
        )
        # this is optional and will be marked as False if not available in argumnets.
        parser.add_argument('--consent_granted', action='store_true')

    def handle(self, *args, **options):
        enterprise_customer_uuid = options['enterprise_customer_uuid']
        enterprise_user_id = options.get('enterprise_user_id')
        is_consent_granted = options.get('consent_granted')

        try:
            enterprise_data.tests.test_utils.EnterpriseLearnerEnrollmentFactory(
                enterprise_customer_uuid=enterprise_customer_uuid,
                enterprise_user_id=enterprise_user_id,
                is_consent_granted=is_consent_granted,
            )
            info = (
                '\nCreated EnterpriseLearnerEnrollment with enterprise_customer_uuid '
                '{} for EnterpriseUser with enterprise_user_id of {} and consent {}\n\n'.format(
                    enterprise_customer_uuid,
                    enterprise_user_id,
                    is_consent_granted,
                )
            )
            sys.stdout.write(info)
        except Exception as exc:
            info = (
                'Error trying to create EnterpriseUser with uuid '
                '{}: {}'.format(enterprise_customer_uuid, exc)
            )
            raise CommandError(info) from exc
