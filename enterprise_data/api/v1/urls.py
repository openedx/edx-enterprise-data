"""
URL definitions for enterprise data api v1.
"""


from rest_framework.routers import DefaultRouter

from enterprise_data.api.v1 import views

app_name = 'enterprise_data_api_v1'

router = DefaultRouter()
router.register(
    r'enterprise/(?P<enterprise_id>.+)/enrollments',
    views.EnterpriseLearnerEnrollmentViewSet,
    'enterprise-learner-enrollment',
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

urlpatterns = router.urls
