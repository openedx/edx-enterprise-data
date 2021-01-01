"""
URL definitions for enterprise data api version 1 endpoint.
"""


from rest_framework.routers import DefaultRouter

from enterprise_data.api.v0 import views

app_name = 'enterprise_data_api_v0'

router = DefaultRouter()
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
