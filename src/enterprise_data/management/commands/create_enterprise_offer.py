"""
management command for creating dummy enterprise offers.
"""


import sys

from django.core.management.base import BaseCommand, CommandError

import enterprise_data.tests.test_utils


class Command(BaseCommand):
    """ management command class """
    help = 'Creates an EnterpriseOffer with randomized attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            'enterprise_customer_uuid',
            type=str,
            help='UUID for an enterprise'
        )

    def handle(self, *args, **options):
        enterprise_customer_uuid = options['enterprise_customer_uuid']

        try:
            enterprise_data.tests.test_utils.EnterpriseOfferFactory(
                enterprise_customer_uuid=enterprise_customer_uuid,
            )
            info = (
                f'Created EnterpriseOffer for enterprise {enterprise_customer_uuid}\n'
            )
            sys.stdout.write(info)
        except Exception as exc:
            info = (
                f'Error trying to create EnterpriseOffer for enterprise {enterprise_customer_uuid}\n'
            )
            raise CommandError(info) from exc
