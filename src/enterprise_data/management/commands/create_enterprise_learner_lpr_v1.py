"""
Management command for creating enterprise learner.
"""


import sys

from django.core.management.base import BaseCommand, CommandError

import enterprise_data.tests.test_utils


class Command(BaseCommand):
    """
    Management command for creating `EnterpriseLearner` instances for dummy data for learner progress report (LPR) V1.
    """
    help = 'Creates an EnterpriseLearner with randomized data.'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_customer_uuid',
            type=str,
            help='UUID for an enterprise'
        )

    def handle(self, *args, **options):
        enterprise_customer_uuid = options['enterprise_customer_uuid']
        try:
            ent_user = enterprise_data.tests.test_utils.EnterpriseLearnerFactory(
                enterprise_customer_uuid=enterprise_customer_uuid
            )
        except Exception as exc:
            info = (
                'Error trying to create EnterpriseLearner with uuid '
                '{}: {}'.format(enterprise_customer_uuid, exc)
            )
            raise CommandError(info) from exc

        info = '\n\nCreated EnterpriseLearner with id {} for enterprise with uuid {}\n'.format(
            ent_user.enterprise_user_id,
            ent_user.enterprise_customer_uuid
        )
        sys.stdout.write(info)

        # TODO: Need to update this to the correct comment for LPR V1 once that is added.
        info = (
            'You can create some enrollments for this user by running the following '
            'command:\n\n    ./manage.py create_enterprise_learner_enrollment_lpr_v1 {} {}\n\n'.format(
                ent_user.enterprise_customer_uuid,
                ent_user.enterprise_user_id,
            )
        )
        sys.stdout.write(info)
