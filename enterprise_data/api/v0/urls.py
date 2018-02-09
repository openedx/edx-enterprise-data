# -*- coding: utf-8 -*-
"""
URL definitions for enterprise data api version 1 endpoint.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from enterprise_data.api.v0 import views

urlpatterns = [
    url(r'^enterprise/(?P<enterprise_id>.+)/enrollments/$',
        views.EnterpriseEnrollmentsView.as_view(),
        name='enterprise_enrollments'),
]
