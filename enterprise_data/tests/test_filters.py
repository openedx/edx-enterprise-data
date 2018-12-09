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
from test_utils import UserFactory


class TestConsentGrantedFilterBackend(APITestCase):
    """
    Test suite for the ``TestConsentGrantedFilterBackend`` filter.
    """
    fixtures = ('enterprise_enrollment', 'enterprise_user', )

    def setUp(self):
        super(TestConsentGrantedFilterBackend, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('v0:enterprise-enrollments-list',
                           kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})

    @mock.patch('enterprise_data.permissions.EnterpriseApiClient')
    def test_filter_for_list(self, mock_enterprise_api_client):
        """
        Filter users through email/username if requesting user is staff, otherwise based off of request user ID.
        """
        mock_enterprise_api_client.return_value.get_with_access_to.return_value = {
            'uuid': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        }
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Fixture data for enterprise 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c' contains 3 objects but only 3 with consent
        assert EnterpriseEnrollment.objects.filter(enterprise_id='ee5e6b3a-069a-4947-bb8d-d2dbc323396c').count() == 3
        assert len(data['results']) == 2
