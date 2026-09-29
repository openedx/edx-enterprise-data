# pylint: skip-file
"""
Enterprise Data Django application initialization.
"""

from django.apps import AppConfig


class EnterpriseDataAppConfig(AppConfig):
    """
    Configuration for the enterprise Django application.
    """

    name = "enterprise_data"

    def ready(self) -> None:
        """
        Perform tasks when the Django application is ready.
        """
        import enterprise_data.signals
