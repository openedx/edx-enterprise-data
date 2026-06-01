"""
Tests for views in the `enterprise_data` module.
"""

import datetime
import importlib
import os
import sys
import types
from unittest import mock
from uuid import UUID, uuid4

import ddt
from pytest import mark
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from django.utils import timezone

from enterprise_data.api.v1.serializers import EnterpriseOfferSerializer
from enterprise_data.api.v1.views.enterprise_learner import EnterpriseLearnerEnrollmentViewSet
from enterprise_data.models import EnterpriseLearnerEnrollment, EnterpriseOffer
from enterprise_data.tests.factories import (
    EnterpriseAdminLearnerProgressFactory,
    EnterpriseAdminSummarizeInsightsFactory,
)
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import (
    EnterpriseLearnerEnrollmentFactory,
    EnterpriseLearnerFactory,
    EnterpriseOfferFactory,
    UserFactory,
    get_dummy_enterprise_api_data,
)
from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment


def _ensure_course_overview_import_for_tests():
    """
    Provide a minimal ``openedx...course_overviews.models`` shim for local
    unit tests when full edx-platform Python dependencies are unavailable.
    """
    try:
        course_overview_models = importlib.import_module(
            'openedx.core.djangoapps.content.course_overviews.models'
        )
        if getattr(course_overview_models, 'CourseOverview', None) is not None:
            return
    except ImportError:
        pass

    module_names = [
        'openedx',
        'openedx.core',
        'openedx.core.djangoapps',
        'openedx.core.djangoapps.content',
        'openedx.core.djangoapps.content.course_overviews',
    ]
    for module_name in module_names:
        if module_name not in sys.modules:
            sys.modules[module_name] = types.ModuleType(module_name)

    models_module_name = 'openedx.core.djangoapps.content.course_overviews.models'
    models_module = types.ModuleType(models_module_name)

    class _Meta:
        db_table = 'course_overviews_courseoverview'

    class DummyCourseOverview:
        _meta = _Meta()

    models_module.CourseOverview = DummyCourseOverview
    sys.modules[models_module_name] = models_module


_ensure_course_overview_import_for_tests()


@ddt.ddt
@mark.django_db
class TestEnterpriseLearnerEnrollmentViewSet(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseLearnerEnrollmentViewSet.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

        mocked_get_enterprise_customer = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer',
            return_value=get_dummy_enterprise_api_data()
        )

        self.mocked_get_enterprise_customer = mocked_get_enterprise_customer.start()
        self.addCleanup(mocked_get_enterprise_customer.stop)
        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseLearnerEnrollment.objects.all().delete()

    def test_filter_by_offer_id(self):
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )

        offer_1_id = '1234'
        offer_2_id = '2ThisIsmyOfferId'

        learner_enrollment_1 = EnterpriseLearnerEnrollmentFactory(
            offer_id=offer_1_id,
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id
        )
        EnterpriseLearnerEnrollmentFactory(
            offer_id=offer_2_id,
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id
        )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'offer_id': offer_1_id})
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['enrollment_id'], learner_enrollment_1.enrollment_id)

    def test_filter_by_ignore_null_course_list_price(self):
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )

        EnterpriseLearnerEnrollmentFactory(
            course_list_price=None,
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id
        )
        learner_enrollment_with_price = EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id
        )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'ignore_null_course_list_price': True})
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['enrollment_id'], learner_enrollment_with_price.enrollment_id)

    def test_get_course_product_line(self):
        """ Test that the course product line information is returned correctly """
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )
        learner_enrollment_executive_ed = EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            course_product_line='Executive Education'
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            course_product_line='OCM'
        )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'course_product_line': 'Executive Education'})
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['enrollment_id'], learner_enrollment_executive_ed.enrollment_id)

    def test_get_subsidy_flag(self):
        """ Test that the subsidy information is returned correctly """
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )
        learner_enrollment_subsidized = EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            is_subsidy=True
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            is_subsidy=False
        )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'is_subsidy': True})
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['enrollment_id'], learner_enrollment_subsidized.enrollment_id)

    def test_search_by_course_title(self):
        """Test that the course title search works correctly"""
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )
        course_titles = ['Introduction to Python', 'Introduction to Java', 'Introduction to C++']

        for title in course_titles:
            EnterpriseLearnerEnrollmentFactory(
                enterprise_customer_uuid=self.enterprise_id,
                is_consent_granted=True,
                enterprise_user_id=enterprise_learner.enterprise_user_id,
                course_title=title,
            )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'search_all': 'Introduction to'})
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_search_by_email(self):
        """Test that the email search works correctly"""
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email="johndoe@example.com"
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            course_title="Sample course",
            user_email="johndoe@example.com"
        )
        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'search_all': 'john'})
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_search_no_results(self):
        """Test that the search returns no results if no matches are found"""
        EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email="test@example.com"
        )
        search_term = 'nonexistentemail@example.com'
        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, data={'search_all': search_term})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.SnowflakeCourseProgressSource')
    def test_list_enriches_course_progress_from_snowflake(self, mock_source_cls):
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email='johndoe@example.com',
        )
        enrollment = EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            user_email='johndoe@example.com',
            courserun_key='course-v1:edX+Demo+2024',
        )
        mock_source_cls.return_value.get_course_progress_map.return_value = {
            ('johndoe@example.com', 'course-v1:edX+Demo+2024'): 0.87,
        }

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['enrollment_id'], enrollment.enrollment_id)
        self.assertEqual(response.data['results'][0]['course_progress'], 0.87)

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.SnowflakeCourseProgressSource')
    def test_list_returns_200_when_snowflake_enrichment_fails(self, mock_source_cls):
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email='johndoe@example.com',
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            user_email='johndoe@example.com',
            courserun_key='course-v1:edX+Demo+2024',
        )
        mock_source_cls.return_value.get_course_progress_map.side_effect = RuntimeError('Snowflake unavailable')

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['results'][0]['course_progress'])

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.SnowflakeCourseProgressSource')
    def test_enrich_course_progress_returns_when_no_results(self, mock_source_cls):
        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])
        mock_source_cls.assert_not_called()

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.SnowflakeCourseProgressSource')
    def test_stream_serialized_data_enriches_course_progress_from_snowflake(self, mock_source_cls):
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email='johndoe@example.com',
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            user_email='johndoe@example.com',
            courserun_key='course-v1:edX+Demo+2024',
        )
        mock_source_cls.return_value.get_course_progress_map.return_value = {
            ('johndoe@example.com', 'course-v1:edX+Demo+2024'): 0.87,
        }

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url, HTTP_ACCEPT='text/csv')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b''.join(response.streaming_content).decode('utf-8')
        # course_progress column should appear in the CSV header and data rows
        self.assertIn('course_progress', content)
        self.assertIn('0.87', content)

    def test_course_passing_grade_field_in_response(self):
        """Test that course_passing_grade field is included in the API response"""
        enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id,
            user_email='student@example.com',
        )
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id,
            user_email='student@example.com',
            courserun_key='course-v1:edX+Demo+2024',
        )

        url = reverse('v1:enterprise-learner-enrollment-list', kwargs={'enterprise_id': self.enterprise_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        # Verify course_passing_grade field is present in the response
        self.assertIn('course_passing_grade', results[0])
        # The field will be null since CourseOverview is mocked in tests
        self.assertIsNone(results[0]['course_passing_grade'])

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.CourseOverview', None)
    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.EnterpriseLearnerEnrollment.objects.filter')
    def test_get_enrollments_with_course_metadata_without_course_overview(self, mock_filter):
        viewset = EnterpriseLearnerEnrollmentViewSet()
        enrollments = mock.Mock()
        with_progress = mock.Mock()
        with_passing_grade = mock.Mock()

        mock_filter.return_value = enrollments
        enrollments.extra.return_value = with_progress
        with_progress.extra.return_value = with_passing_grade

        result = viewset._get_enrollments_with_course_metadata(self.enterprise_id)  # pylint: disable=protected-access

        mock_filter.assert_called_once_with(enterprise_customer_uuid=self.enterprise_id)
        enrollments.extra.assert_called_once_with(select={'course_progress': 'NULL'})
        with_progress.extra.assert_called_once_with(select={'course_passing_grade': 'NULL'})
        self.assertEqual(result, with_passing_grade)

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.cache')
    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.CourseOverview')
    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.connection.introspection.table_names')
    def test_enrich_course_passing_grade_uses_cache(
        self,
        mock_table_names,
        mock_course_overview,
        mock_cache,
    ):
        viewset = EnterpriseLearnerEnrollmentViewSet()
        mock_course_overview._meta.db_table = 'course_overviews_courseoverview'
        mock_table_names.return_value = ['course_overviews_courseoverview']
        mock_cache.get.return_value = mock.Mock(is_found=True, value=0.7)
        rows = [{'courserun_key': 'course-v1:edX+Demo+2024', 'course_passing_grade': None}]

        result = viewset._enrich_course_passing_grade_rows(rows)  # pylint: disable=protected-access

        self.assertEqual(result[0]['course_passing_grade'], 0.7)
        mock_table_names.assert_called_once_with()
        mock_course_overview.objects.filter.assert_not_called()
        mock_cache.set.assert_not_called()

    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.cache')
    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.connection.introspection.table_names')
    @mock.patch('enterprise_data.api.v1.views.enterprise_learner.CourseOverview')
    def test_enrich_course_passing_grade_fetches_and_caches_missing_grade(
        self,
        mock_course_overview,
        mock_table_names,
        mock_cache,
    ):
        viewset = EnterpriseLearnerEnrollmentViewSet()
        mock_course_overview._meta.db_table = 'course_overviews_courseoverview'
        mock_table_names.return_value = ['course_overviews_courseoverview']
        mock_cache.get.return_value = mock.Mock(is_found=False)
        mock_course_overview.objects.filter.return_value.values_list.return_value = [
            ('course-v1:edX+Demo+2024', 0.7),
        ]
        rows = [{'courserun_key': 'course-v1:edX+Demo+2024', 'course_passing_grade': None}]

        result = viewset._enrich_course_passing_grade_rows(rows)  # pylint: disable=protected-access

        self.assertEqual(result[0]['course_passing_grade'], 0.7)
        mock_table_names.assert_called_once_with()
        mock_course_overview.objects.filter.assert_called_once_with(id__in=['course-v1:edX+Demo+2024'])
        mock_cache.set.assert_called_once()


@ddt.ddt
@mark.django_db
class TestEnterpriseOffersViewSet(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseOfferViewSet.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

        self.enterprise_customer_uuid_1 = uuid4()
        self.enterprise_offer_1_offer_id = str(uuid4())
        self.enterprise_offer_1 = EnterpriseOfferFactory(
            offer_id=self.enterprise_offer_1_offer_id.replace('-', ''),
            enterprise_customer_uuid=self.enterprise_customer_uuid_1
        )

        self.enterprise_customer_2_uuid = uuid4()
        self.enterprise_offer_2_offer_id = '11111'
        self.enterprise_offer_2 = EnterpriseOfferFactory(
            offer_id=self.enterprise_offer_2_offer_id,
            enterprise_customer_uuid=self.enterprise_customer_2_uuid
        )

        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseOffer.objects.all().delete()

    def test_list_offers(self):
        enterprise_id = self.enterprise_offer_1.enterprise_customer_uuid
        url = reverse(
            'v1:enterprise-offers-list',
            kwargs={'enterprise_id': enterprise_id}
        )

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        expected_results = [EnterpriseOfferSerializer(self.enterprise_offer_1).data]
        response_json = response.json()
        results = response_json['results']
        assert results == expected_results

    def test_retrieve_offers_uuid(self):
        """
        Make sure that EnterpriseOffer objects that store UUID values inside offer_id return a hyphenated UUID.
        """
        enterprise_id = self.enterprise_offer_1.enterprise_customer_uuid
        url = os.path.join(
            reverse(
                'v1:enterprise-offers-list',
                kwargs={'enterprise_id': enterprise_id}
            ),
            self.enterprise_offer_1_offer_id + "/",
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        results = response_json
        assert results['offer_id'] == str(UUID(self.enterprise_offer_1_offer_id))

    def test_retrieve_offer_offer_id_int(self):
        """
        Make sure that EnterpriseOffer objects that store integer values inside offer_id return the value verbatim.
        """
        enterprise_id = self.enterprise_offer_2.enterprise_customer_uuid
        url = os.path.join(
            reverse(
                'v1:enterprise-offers-list',
                kwargs={'enterprise_id': enterprise_id}
            ),
            self.enterprise_offer_2_offer_id + "/",
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        results = response_json
        assert results['offer_id'] == self.enterprise_offer_2_offer_id


@ddt.ddt
@mark.django_db
class TestEnterpriseAdminInsightsView(JWTTestMixin, APITransactionTestCase):
    """
    Tests for EnterpriseAdminInsightsView.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.enterprise_customer_uuid_1 = uuid4()
        self.enterprise_customer_uuid_2 = uuid4()
        self.set_jwt_cookie(context=f'{self.enterprise_customer_uuid_1}')

    def verify_data(self, received, expected):
        """
        Verify that received and expected data are same.
        """
        received_keys = received.keys()
        for key in received_keys:
            expected_value = getattr(expected, key)
            if isinstance(expected_value, UUID):
                expected_value = str(expected_value)
            if isinstance(expected_value, datetime.datetime):
                expected_value = expected_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            assert received[key] == expected_value

    def test_retrieve_enterprise_admin_insights(self):
        """
        Verify that `EnterpriseAdminInsightsView` gives correct response if the user has access to enterprise.
        """
        enterprise_customer_uuid = self.enterprise_customer_uuid_1
        learner_progress_obj = EnterpriseAdminLearnerProgressFactory.create(
            enterprise_customer_uuid=enterprise_customer_uuid
        )
        learner_engagement_obj = EnterpriseAdminSummarizeInsightsFactory.create(
            enterprise_customer_uuid=enterprise_customer_uuid
        )

        url = reverse('v1:enterprise-admin-insights', kwargs={'enterprise_id': enterprise_customer_uuid})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()

        learner_progress = response_json['learner_progress']
        self.verify_data(learner_progress, learner_progress_obj)
        learner_engagement = response_json['learner_engagement']
        self.verify_data(learner_engagement, learner_engagement_obj)

    def test_retrieve_enterprise_admin_insights_no_data(self):
        """
        Verify that `EnterpriseAdminInsightsView` gives correct response if the user has access but no data exists.
        """
        url = reverse('v1:enterprise-admin-insights', kwargs={'enterprise_id': self.enterprise_customer_uuid_1})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_enterprise_admin_insights_no_access(self):
        """
        Verify that `EnterpriseAdminInsightsView` give 401 if the user has access to enterprise.
        """
        enterprise_customer_uuid = self.enterprise_customer_uuid_2
        url = reverse('v1:enterprise-admin-insights', kwargs={'enterprise_id': enterprise_customer_uuid})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@ddt.ddt
@mark.django_db
class TestSearchEnrollmentFilter(JWTTestMixin, APITransactionTestCase):
    """
    Tests for filtering enrolled vs unenrolled learners using search_enrollment param.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        role, __ = EnterpriseDataFeatureRole.objects.get_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)
        self.role_assignment = EnterpriseDataRoleAssignment.objects.create(
            role=role,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

        mocked_get_enterprise_customer = mock.patch(
            'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer',
            return_value=get_dummy_enterprise_api_data()
        )
        self.mocked_get_enterprise_customer = mocked_get_enterprise_customer.start()
        self.addCleanup(mocked_get_enterprise_customer.stop)

        self.enterprise_id = 'fd0d9cd4-bc35-45e8-ba35-e73be3fc5a07'
        self.url = reverse(
            'v1:enterprise-learner-enrollment-list',
            kwargs={'enterprise_id': self.enterprise_id}
        )
        self.enterprise_learner = EnterpriseLearnerFactory(
            enterprise_customer_uuid=self.enterprise_id
        )
        self.set_jwt_cookie()

    def tearDown(self):
        super().tearDown()
        EnterpriseLearnerEnrollment.objects.all().delete()

    def create_enrolled(self):
        """Enrollment with unenrollment_date = NULL"""
        return EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            enterprise_user_id=self.enterprise_learner.enterprise_user_id,
            unenrollment_date=None,
        )

    def create_unenrolled(self, dt=None):
        """Enrollment with unenrollment_date != NULL"""
        dt = dt or timezone.now()
        return EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=self.enterprise_id,
            enterprise_user_id=self.enterprise_learner.enterprise_user_id,
            unenrollment_date=dt,
        )

    def test_filter_enrolled(self):
        """Test for enrolled learners"""
        # Create enrolled learner (unenrollment_date = NULL)
        enrolled = self.create_enrolled()
        # Unenrolled learner(NOT NULL)
        self.create_unenrolled()

        response = self.client.get(
            self.url,
            data={"search_enrollment": "enrolled"}
        )

        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["enrollment_id"], enrolled.enrollment_id)

    def test_filter_unenrolled(self):
        """Test for unenrolled learners"""
        # Enrolled learner (NULL)
        self.create_enrolled()
        # Unenrolled learner (NOT NULL)
        unenrolled = self.create_unenrolled()

        response = self.client.get(
            self.url,
            data={"search_enrollment": "unenrolled"}
        )

        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["enrollment_id"], unenrolled.enrollment_id)

    def test_no_search_enrollment_filter(self):
        """Test no filter - return all items"""
        self.create_enrolled()
        self.create_unenrolled()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

    def test_invalid_search_enrollment_value(self):
        """Invalid value → return all"""
        self.create_enrolled()
        self.create_unenrolled()

        response = self.client.get(
            self.url,
            data={"search_enrollment": "not-valid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)
