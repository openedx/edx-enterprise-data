"""
Enterprise data api application. This Django app exposes API endpoints used by enterprises.
"""

from __future__ import absolute_import, unicode_literals

__version__ = "1.0.17"

default_app_config = "enterprise_data.apps.EnterpriseDataAppConfig"  # pylint: disable=invalid-name


def update_settings(django_settings):
    """Set enterprise_data settings."""
    django_settings.INSTALLED_APPS = django_settings.INSTALLED_APPS + ("rules.apps.AutodiscoverRulesConfig",)
    django_settings.AUTHENTICATION_BACKENDS.insert(0, "rules.permissions.ObjectPermissionBackend")
