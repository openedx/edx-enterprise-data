"""
URL definitions for enterprise data api v1.
"""


from rest_framework.routers import DefaultRouter

from django.urls import re_path

from enterprise_data.api.v1.views import enterprise_admin as enterprise_admin_views
from enterprise_data.api.v1.views import enterprise_learner as enterprise_learner_views
from enterprise_data.api.v1.views import enterprise_offers as enterprise_offers_views
from enterprise_data.api.v1.views.analytics_completions import AdvanceAnalyticsCompletionsView
from enterprise_data.api.v1.views.analytics_engagements import AdvanceAnalyticsEngagementView
from enterprise_data.api.v1.views.analytics_enrollments import AdvanceAnalyticsEnrollmentsView
from enterprise_data.api.v1.views.analytics_leaderboard import AdvanceAnalyticsLeaderboardView
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
router.register(
    r'enterprise/(?P<enterprise_id>.+)/module-performance',
    enterprise_admin_views.EnterpriseExecEdLCModulePerformanceViewSet,
    'enterprise-admin-module-performance',
)

urlpatterns = [
    re_path(
        fr'^admin/insights/(?P<enterprise_id>{UUID4_REGEX})$',
        enterprise_admin_views.EnterpriseAdminInsightsView.as_view(),
        name='enterprise-admin-insights'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_id>{UUID4_REGEX})$',
        enterprise_admin_views.EnterpriseAdminAnalyticsAggregatesView.as_view(),
        name='enterprise-admin-analytics-aggregates'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/leaderboard$',
        AdvanceAnalyticsLeaderboardView.as_view({'get': 'list'}),
        name='enterprise-admin-analytics-leaderboard-list'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/enrollments/stats$',
        AdvanceAnalyticsEnrollmentsView.as_view({'get': 'stats'}),
        name='enterprise-admin-analytics-enrollments-stats'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/enrollments$',
        AdvanceAnalyticsEnrollmentsView.as_view({'get': 'list'}),
        name='enterprise-admin-analytics-enrollments'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/completions/stats$',
        AdvanceAnalyticsCompletionsView.as_view({'get': 'stats'}),
        name='enterprise-admin-analytics-completions-stats'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/completions$',
        AdvanceAnalyticsCompletionsView.as_view({'get': 'list'}),
        name='enterprise-admin-analytics-completions'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/engagements/stats$',
        AdvanceAnalyticsEngagementView.as_view({'get': 'stats'}),
        name='enterprise-admin-analytics-engagements-stats'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_uuid>{UUID4_REGEX})/engagements$',
        AdvanceAnalyticsEngagementView.as_view({'get': 'list'}),
        name='enterprise-admin-analytics-engagements'
    ),
    re_path(
        fr'^admin/analytics/(?P<enterprise_id>{UUID4_REGEX})/skills/stats',
        enterprise_admin_views.EnterpriseAdminAnalyticsSkillsView.as_view(),
        name='enterprise-admin-analytics-skills'
    ),
    re_path(
        fr'^enterprise/(?P<enterprise_uuid>{UUID4_REGEX})/budgets',
        enterprise_admin_views.EnterpriseBudgetView.as_view(),
        name='enterprise-budgets'
    ),
    re_path(
        fr'^enterprise/(?P<enterprise_uuid>{UUID4_REGEX})/groups',
        enterprise_admin_views.EnterpriseGroupMembershipView.as_view(),
        name='enterprise-groups'
    ),
]

urlpatterns += router.urls
