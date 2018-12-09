"""
Enterprise_data url configuration.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

urlpatterns = [
    url(
        r'^enterprise/api/',
        include('enterprise_data.api.urls'),
        name='enterprise_data_api'
    ),
]
