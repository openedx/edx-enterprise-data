"""
management command for creating enterprise users
"""
from __future__ import absolute_import, unicode_literals

import sys

from django.core.management.base import BaseCommand, CommandError

import enterprise_data.tests.test_utils


class Command(BaseCommand):
    """ management command class """
    help = 'Creates an EnterpriseUser with randomized attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_id',
            type=str,
            help='UUID for an enterprise'
        )

    def handle(self, *args, **options):
        enterprise_id = options['enterprise_id']
        try:
            ent_user = enterprise_data.tests.test_utils.EnterpriseUserFactory(
                enterprise_id=enterprise_id
            )
        except Exception as exc:
            info = (
                'Error trying to create EnterpriseUser with uuid '
                '{}: {}'.format(enterprise_id, exc)
            )
            raise CommandError(info)

        info = '\n\nCreated EnterpriseUser with id {} for enterprise with uuid {}\n'.format(
            ent_user.enterprise_user_id,
            ent_user.enterprise_id
        )
        sys.stdout.write(info)

        info = (
            'You can create some enrollments for this user by running the following '
            'command:\n\n    ./manage.py create_enterprise_enrollment {} {}\n\n'.format(
                ent_user.enterprise_id,
                ent_user.enterprise_user_id,
            )
        )
        sys.stdout.write(info)
