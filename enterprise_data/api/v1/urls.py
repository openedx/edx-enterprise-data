"""
URL definitions for enterprise data api v1.
"""


from rest_framework.routers import DefaultRouter

from django.urls import re_path

from enterprise_data.api.v1 import views
from enterprise_data.constants import UUID4_REGEX

app_name = 'enterprise_data_api_v1'

router = DefaultRouter()
router.register(
    r'enterprise/(?P<enterprise_id>.+)/enrollments',
    views.EnterpriseLearnerEnrollmentViewSet,
    'enterprise-learner-enrollment',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/offers',
    views.EnterpriseOfferViewSet,
    'enterprise-offers',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/users',
    views.EnterpriseLearnerViewSet,
    'enterprise-learner',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/learner_completed_courses',
    views.EnterpriseLearnerCompletedCoursesViewSet,
    'enterprise-learner-completed-courses',
)

urlpatterns = [
    re_path(
        fr'^admin/insights/(?P<enterprise_id>{UUID4_REGEX})$',
        views.EnterpriseAdminInsightsView.as_view(),
        name='enterprise-admin-insights'
    ),
]

urlpatterns += router.urls
