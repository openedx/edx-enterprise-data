# -*- coding: utf-8 -*-
"""
URL definitions for enterprise data API endpoint.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

urlpatterns = [
    url(r'^v0/', include('enterprise_data.api.v0.urls', 'v0'), name='api_v0'),
]
