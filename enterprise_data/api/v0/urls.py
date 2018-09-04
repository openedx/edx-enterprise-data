# -*- coding: utf-8 -*-
"""
URL definitions for enterprise data api version 1 endpoint.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework.routers import DefaultRouter

from enterprise_data.api.v0 import views

router = DefaultRouter()  # pylint: disable=invalid-name
router.register(
    r'enterprise/(?P<enterprise_id>.+)/enrollments',
    views.EnterpriseEnrollmentsViewSet,
    'enterprise-enrollments',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/users',
    views.EnterpriseUsersViewSet,
    'enterprise-users',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/learner_completed_courses',
    views.EnterpriseLearnerCompletedCoursesViewSet,
    'enterprise-learner-completed-courses',
)

urlpatterns = router.urls
