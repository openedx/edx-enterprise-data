"""
management command for creating enterprise enrollments
"""

import sys

from django.core.management.base import BaseCommand, CommandError

import enterprise_data.tests.test_utils


class Command(BaseCommand):
    """management command class"""

    help = "Creates an EnterpriseEnrollment with randomized attributes"

    def add_arguments(self, parser):
        parser.add_argument("enterprise_id", type=str, help="UUID for an enterprise")
        parser.add_argument(
            "enterprise_user_id", type=int, default=None, help="enterprise_user_id for an enterprise_user"
        )

    def handle(self, *args, **options):
        enterprise_id = options["enterprise_id"]
        enterprise_user_id = options.get("enterprise_user_id")
        try:
            enterprise_data.tests.test_utils.EnterpriseEnrollmentFactory(
                enterprise_id=enterprise_id,
                enterprise_user_id=enterprise_user_id,
            )
            info = (
                "\nCreated EnterpriseEnrollment with enterprise_id "
                f"{enterprise_id} for EnterpriseUser with enterprise_user_id of {enterprise_user_id}\n\n"
            )
            sys.stdout.write(info)
        except Exception as exc:
            info = f"Error trying to create EnterpriseUser with uuid {enterprise_id}: {exc}"
            raise CommandError(info) from exc
