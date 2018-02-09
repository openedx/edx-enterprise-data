# -*- coding: utf-8 -*-
"""
Tests for filters in enterprise_data.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from enterprise_data.models import EnterpriseEnrollment
from test_utils import UserFactory


class TestConsentGrantedFilterBackend(APITestCase):
    """
    Test suite for the ``TestConsentGrantedFilterBackend`` filter.
    """
    fixtures = ('enterprise_enrollment',)

    def setUp(self):
        super(TestConsentGrantedFilterBackend, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('v0:enterprise_enrollments',
                           kwargs={'enterprise_id': 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'})

    def test_filter_for_list(self):
        """
        Filter users through email/username if requesting user is staff, otherwise based off of request user ID.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Fixture data for enterprise 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c' contains 2 objects but only 1 with consent
        assert EnterpriseEnrollment.objects.filter(enterprise_id='ee5e6b3a-069a-4947-bb8d-d2dbc323396c').count() == 2
        assert len(data['results']) == 1
