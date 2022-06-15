"""
Tests for the `edx-enterprise` api v1 serializer module.
"""

import ddt
from pytest import mark
from rest_framework.test import APITransactionTestCase

from enterprise_data.api.v1.serializers import EnterpriseLearnerEnrollmentSerializer
from enterprise_data.tests.test_utils import EnterpriseLearnerEnrollmentFactory, EnterpriseLearnerFactory


@mark.django_db
@ddt.ddt
class TestEnterpriseLearnerEnrollmentSerializer(APITransactionTestCase):
    """
    Tests for `enterprise_learner_enrollment` API serializer.
    """

    def setUp(self):
        super().setUp()
        ent_user = EnterpriseLearnerFactory()
        self.enrollment = EnterpriseLearnerEnrollmentFactory(
            enterprise_user_id=ent_user.enterprise_user_id,
            is_consent_granted=True
        )

    @ddt.data(
        (0.0, 0.0),
        (3600, 1.0),
    )
    @ddt.unpack
    def test_total_learning_time_hours(self, total_learning_time_seconds, expected_total_learning_time_seconds):
        self.enrollment.total_learning_time_seconds = total_learning_time_seconds
        self.enrollment.save()
        serializer = EnterpriseLearnerEnrollmentSerializer(self.enrollment)
        assert serializer.data['total_learning_time_hours'] == expected_total_learning_time_seconds
