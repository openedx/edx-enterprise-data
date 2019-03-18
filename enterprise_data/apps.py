# -*- coding: utf-8 -*-
"""
Enterprise Data Django application initialization.
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.conf import settings


class EnterpriseDataAppConfig(AppConfig):
    """
    Configuration for the enterprise Django application.
    """

    name = "enterprise_data"

    def ready(self):
        self._update_settings()

    def _update_settings(self):
        from enterprise_data import update_settings
        update_settings(settings)
