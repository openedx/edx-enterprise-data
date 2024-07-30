"""
Tests for filters in enterprise_data.
"""

from unittest import mock
from urllib.parse import urljoin

import responses
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from django.conf import settings

from enterprise_data.api.v1.views.enterprise_learner import EnterpriseLearnerViewSet
from enterprise_data.filters import AuditUsersEnrollmentFilterBackend
from enterprise_data.models import EnterpriseEnrollment, EnterpriseLearnerEnrollment
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import EnterpriseLearnerEnrollmentFactory, EnterpriseLearnerFactory, UserFactory


class TestConsentGrantedFilterBackend(JWTTestMixin, APITestCase):
    """
    Test suite for the ``TestConsentGrantedFilterBackend`` filter.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.url = reverse('v0:enterprise-enrollments-list',
                           kwargs={'enterprise_id': self.enterprise_id})
        self.set_jwt_cookie(context=self.enterprise_id)

    def mock_enterprise_api_client_response(self, enforce_dsc=None):
        """
        Mocks enterprise api client response.
        """
        mock_path = 'enterprise_data.filters.EnterpriseApiClient.get_enterprise_customer'
        with mock.patch(mock_path) as mock_enterprise_api_client:
            mock_enterprise_api_client.return_value = {
                'uuid': self.enterprise_id,
                'enable_audit_data_reporting': True,
                'enforce_data_sharing_consent': enforce_dsc or True,
            }
            return self.client.get(self.url)

    def test_filter_for_list(self):
        """
        Filter users through email/username if requesting user is staff, otherwise based off of request user ID.
        """
        response = self.mock_enterprise_api_client_response()

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Fixture data for enterprise 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c' contains 3 objects but only 2 with consent
        assert EnterpriseEnrollment.objects.filter(enterprise_id=self.enterprise_id).count() == 3
        assert len(data['results']) == 2

    def test_filter_with_external_consent(self):
        """
        If the enterprise is configured for externally managed data consent, all enrollments will be returned.
        """
        response = self.mock_enterprise_api_client_response('externally_managed')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Fixture data for enterprise 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c' contains 3 objects but only 2 with consent
        assert EnterpriseEnrollment.objects.filter(enterprise_id=self.enterprise_id).count() == 3
        assert len(data['results']) == 3


class TestAuditUsersEnrollmentFilterBackend(JWTTestMixin, APITestCase):
    """
    Test suite for the ``AuditUsersEnrollmentFilterBackend``.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.enterprise1_uuid = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        self.enterprise2_uuid = '0395b02f-6b29-42ed-9a41-45f3dff8349c'
        self.set_jwt_cookie(context=self.enterprise1_uuid)
        self.set_jwt_cookie(context=self.enterprise2_uuid)

    def mock_enterprise_api_endpoints(self, enterprise_uuid, enable_audit_data_reporting=True):
        """
        Mock enterprise api endpoints.
        """
        responses.add(
            responses.POST,
            urljoin(settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL + '/', 'access_token'),
            status=200,
            json={
                'access_token': 'test_access_token',
                'expires_in': 3600,
            },
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            urljoin(settings.LMS_BASE_URL + '/', f'enterprise/api/v1/enterprise-customer/{enterprise_uuid}'),
            json={
                'uuid': enterprise_uuid,
                'enable_audit_data_reporting': enable_audit_data_reporting,
                'enforce_data_sharing_consent': True,
            },
            status=200,
            content_type='application/json'
        )

    @responses.activate
    def test_filter_with_audit_reporting_enabled(self):
        """
        Verify that expected response is returned when `enable_audit_data_reporting` set to True.
        """
        enterprise_uuid = self.enterprise1_uuid
        enterprise_learner = EnterpriseLearnerFactory(enterprise_customer_uuid=enterprise_uuid)
        EnterpriseLearnerEnrollmentFactory.create_batch(
            2,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner.enterprise_user_id
        )

        queryset = EnterpriseLearnerEnrollment.objects.all()
        request = APIRequestFactory().get('/')
        view = EnterpriseLearnerViewSet(kwargs={'enterprise_id': enterprise_uuid})
        filter_backend = AuditUsersEnrollmentFilterBackend()

        self.mock_enterprise_api_endpoints(enterprise_uuid=enterprise_uuid)

        filtered_queryset = filter_backend.filter_queryset(request, queryset, view)
        assert filtered_queryset == queryset

    @responses.activate
    def test_filter_without_audit_reporting_enabled(self):
        """
        Verify that expected response is returned when `enable_audit_data_reporting` set to False.
        """
        enterprise_uuid = self.enterprise2_uuid
        enterprise_learner_1 = EnterpriseLearnerFactory(enterprise_customer_uuid=enterprise_uuid)
        learner_enrollment_1 = EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=enterprise_uuid,
            is_consent_granted=True,
            enterprise_user_id=enterprise_learner_1.enterprise_user_id
        )

        enterprise_learner_2 = EnterpriseLearnerFactory(enterprise_customer_uuid=enterprise_uuid)
        EnterpriseLearnerEnrollmentFactory(
            enterprise_customer_uuid=enterprise_uuid,
            is_consent_granted=True,
            user_current_enrollment_mode='audit',
            enterprise_user_id=enterprise_learner_2.enterprise_user_id
        )

        queryset = EnterpriseLearnerEnrollment.objects.all()
        request = APIRequestFactory().get('/')
        view = EnterpriseLearnerViewSet(kwargs={'enterprise_id': enterprise_uuid})
        filter_backend = AuditUsersEnrollmentFilterBackend()

        self.mock_enterprise_api_endpoints(enterprise_uuid=enterprise_uuid, enable_audit_data_reporting=False)

        filtered_queryset = filter_backend.filter_queryset(request, queryset, view)
        assert filtered_queryset.count() == 1
        assert filtered_queryset.first().enterprise_enrollment_id == learner_enrollment_1.enterprise_enrollment_id
        assert filtered_queryset.first().user_current_enrollment_mode != 'audit'
