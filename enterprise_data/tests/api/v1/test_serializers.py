"""
Tests for the `edx-enterprise` api v1 serializer module.
"""

import uuid

import ddt
from pytest import mark
from rest_framework.test import APITransactionTestCase

from enterprise_data.api.v1.serializers import EnterpriseLearnerEnrollmentSerializer, EnterpriseOfferSerializer
from enterprise_data.tests.test_utils import (
    EnterpriseLearnerEnrollmentFactory,
    EnterpriseLearnerFactory,
    EnterpriseOfferFactory,
)


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


@ddt.ddt
class TestEnterpriseOfferSerializer(APITransactionTestCase):
    """
    Tests for `enterprise_offer` API serializer.
    """

    @ddt.data(
        ('787f0fa7-f89a-4267-9e2b-fcd299e83918', '787f0fa7f89a42679e2bfcd299e83918'),
        ('56a779a5-21ec-4711-830f-6654d3faaa5f', '56a779a521ec4711830f6654d3faaa5f'),
        ('12345', '12345'),
    )
    @ddt.unpack
    def test_deserialize_offer_id_valid(self, offer_id_request, offer_id_db):
        data = {
            'offer_id': offer_id_request,
            'enterprise_customer_uuid': str(uuid.uuid4()),
        }
        serialized_offer = EnterpriseOfferSerializer(data=data)
        assert serialized_offer.is_valid()
        assert serialized_offer.validated_data['offer_id'] == offer_id_db

    @ddt.data(
        # Representations that could be real UUIDs should always be normalized to un-hyphenated UUIDs.
        ('787f0fa7f89a42679e2bfcd299e83918', '787f0fa7-f89a-4267-9e2b-fcd299e83918'),
        ('f0d5fcdbed8e4d408f3b79d1671f967f', 'f0d5fcdb-ed8e-4d40-8f3b-79d1671f967f'),
        ('c1d39f8a3fd246758bf7f56dd076694d', 'c1d39f8a-3fd2-4675-8bf7-f56dd076694d'),
        ('12345', '12345'),
    )
    @ddt.unpack
    def test_serialize_offer_id_valid(self, offer_id_db, offer_id_serialized):
        offer = EnterpriseOfferFactory(offer_id=offer_id_db)
        serialized_offer = EnterpriseOfferSerializer(offer)
        assert serialized_offer.data['offer_id'] == offer_id_serialized

    @ddt.data(
        # The following should fail validation because we want to avoid storing these into the DB.
        None,  # null values not allowed.
        '',  # empty values not allowed.
        'abc',  # Not exactly 36 characters but also obviously not an integer.
        '787f0fa7f89a42679e2bfcd299e83918',  # Not exactly 36 characters but also obviously not an integer.
        '11111111111',  # greater than 10 digit integer
        '111111111111111111111111111111111111',  # 36 digit integer
        '11111111111111111111111111111111',  # 32 digit integer
    )
    def test_deserialize_offer_id_invalid(self, offer_id_request):
        data = {
            'offer_id': offer_id_request,
            'enterprise_customer_uuid': str(uuid.uuid4()),
        }
        serializer = EnterpriseOfferSerializer(data=data)
        assert not serializer.is_valid()
