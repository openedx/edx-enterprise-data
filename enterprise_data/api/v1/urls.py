"""
URL definitions for enterprise data api v1.
"""


from rest_framework.routers import DefaultRouter

from django.urls import re_path

from enterprise_data.api.v1.views import enterprise_admin as enterprise_admin_views
from enterprise_data.api.v1.views import enterprise_learner as enterprise_learner_views
from enterprise_data.api.v1.views import enterprise_offers as enterprise_offers_views
from enterprise_data.constants import UUID4_REGEX

app_name = 'enterprise_data_api_v1'

router = DefaultRouter()
router.register(
    r'enterprise/(?P<enterprise_id>.+)/enrollments',
    enterprise_learner_views.EnterpriseLearnerEnrollmentViewSet,
    'enterprise-learner-enrollment',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/offers',
    enterprise_offers_views.EnterpriseOfferViewSet,
    'enterprise-offers',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/users',
    enterprise_learner_views.EnterpriseLearnerViewSet,
    'enterprise-learner',
)
router.register(
    r'enterprise/(?P<enterprise_id>.+)/learner_completed_courses',
    enterprise_learner_views.EnterpriseLearnerCompletedCoursesViewSet,
    'enterprise-learner-completed-courses',
)

urlpatterns = [
    re_path(
        fr'^admin/insights/(?P<enterprise_id>{UUID4_REGEX})$',
        enterprise_admin_views.EnterpriseAdminInsightsView.as_view(),
        name='enterprise-admin-insights'
    ),
    re_path(
        fr'^admin/anlaytics/(?P<enterprise_id>{UUID4_REGEX})$',
        enterprise_admin_views.EnterpriseAdminAnalyticsAggregatesView.as_view(),
        name='enterprise-admin-analytics-aggregates'
    ),
]

urlpatterns += router.urls
