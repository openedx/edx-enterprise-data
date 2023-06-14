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
        ('787f0fa7-f89a-4267-9e2b-fcd299e83918', '787f0fa7-f89a-4267-9e2b-fcd299e83918'),
        ('787f0fa7f89a42679e2bfcd299e83918', '787f0fa7-f89a-4267-9e2b-fcd299e83918'),
        ('11111111111111111111111111111111', '11111111-1111-1111-1111-111111111111'),
        # fewer or more than 32 characters should serialize into integers.
        ('1111111111111111111111111111111', '1111111111111111111111111111111'),
        ('111111111111111111111111111111111', '111111111111111111111111111111111'),
        # We never want to see the following cases in real life, but at least thye're deterministic and don't crash.
        ('abc', 'abc'),  # Not exactly 32 characters but also obviously not an integer.
        ('', ''),
    )
    @ddt.unpack
    def test_serialize_offer_id(self, offer_id_db, offer_id_serialized):
        offer = EnterpriseOfferFactory(offer_id=offer_id_db)
        serialized_offer = EnterpriseOfferSerializer(offer)
        assert serialized_offer.data['offer_id'] == offer_id_serialized

    @ddt.data(
        # Representations that could be real UUIDs should always be normalized to un-hyphenated UUIDs.
        ('787f0fa7-f89a-4267-9e2b-fcd299e83918', '787f0fa7f89a42679e2bfcd299e83918'),
        ('787f0fa7f89a42679e2bfcd299e83918', '787f0fa7f89a42679e2bfcd299e83918'),
        # hyphens in the wrong place, but gosh dangit this is a valid UUID!
        ('787f0fa7-f89a-4267-9e2bfcd299e8391-8', '787f0fa7f89a42679e2bfcd299e83918'),
        # Representations that are integers should be deserialized verbatim. 31-33 lengths.
        ('1111111111111111111111111111111', '1111111111111111111111111111111'),
        ('11111111111111111111111111111111', '11111111111111111111111111111111'),
        ('111111111111111111111111111111111', '111111111111111111111111111111111'),
    )
    @ddt.unpack
    def test_deserialize_offer_id_valid(self, offer_id_request, offer_id_validated):
        data = {
            'offer_id': offer_id_request,
            'enterprise_customer_uuid': str(uuid.uuid4()),
        }
        serializer = EnterpriseOfferSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['offer_id'] == offer_id_validated

    @ddt.data(
        # The following should fail validation because we want to avoid storing these into the DB.
        None,  # null values not allowed.
        '',  # empty values not allowed.
        'abc',  # Not exactly 32 characters but also obviously not an integer.
    )
    def test_deserialize_offer_id_invalid(self, offer_id_request):
        data = {
            'offer_id': offer_id_request,
            'enterprise_customer_uuid': str(uuid.uuid4()),
        }
        serializer = EnterpriseOfferSerializer(data=data)
        assert not serializer.is_valid()
