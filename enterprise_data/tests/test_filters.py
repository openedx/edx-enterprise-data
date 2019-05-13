# -*- coding: utf-8 -*-
"""
Tests for filters in enterprise_data.
"""
from __future__ import absolute_import, unicode_literals

import mock
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from enterprise_data.models import EnterpriseEnrollment
from enterprise_data.tests.mixins import JWTTestMixin
from enterprise_data.tests.test_utils import UserFactory


class TestConsentGrantedFilterBackend(JWTTestMixin, APITestCase):
    """
    Test suite for the ``TestConsentGrantedFilterBackend`` filter.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super(TestConsentGrantedFilterBackend, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)  # pylint: disable=no-member
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
                'enable_audit_enrollment': True,
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
