"""
Tests for the `enterprise-data` models module.
"""


import unittest

import ddt
from pytest import mark

from enterprise_data.tests.test_utils import EnterpriseEnrollmentFactory, EnterpriseOfferFactory, EnterpriseUserFactory


@mark.django_db
@ddt.ddt
class TestEnterpriseEnrollment(unittest.TestCase):
    """
    Tests for Enterprise Enrollment model
    """

    def setUp(self):
        enterprise_user = EnterpriseUserFactory(enterprise_user_id=1234)
        course_id = 'course-v1:edX+DemoX+DemoCourse'

        self.enrollment = EnterpriseEnrollmentFactory(
            enterprise_user=enterprise_user,
            course_id=course_id
        )
        super().setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = '<Enterprise Enrollment for user 1234 in course-v1:edX+DemoX+DemoCourse>'
        assert expected_str == method(self.enrollment)


@mark.django_db
@ddt.ddt
class TestEnterpriseOffer(unittest.TestCase):
    """
    Tests for Enterprise Offer model
    """

    def setUp(self):
        self.enterprise_offer = EnterpriseOfferFactory(
            enterprise_customer_uuid='ee5e6b3a-069a-4947-bb8d-d2dbc323396c',
            enterprise_name='test-enterprise'
        )
        super().setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = (f'<Enterprise Offer {self.enterprise_offer.offer_id} '
                        f'for {self.enterprise_offer.enterprise_name}>')
        assert expected_str == method(self.enterprise_offer)


@mark.django_db
@ddt.ddt
class TestEnterpriseUser(unittest.TestCase):
    """
    Tests for Enterprise User model
    """
    def setUp(self):
        enterprise_id = 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'
        lms_user_id = 1234
        self.user = EnterpriseUserFactory(lms_user_id=lms_user_id, enterprise_id=enterprise_id)
        super().setUp()

    @ddt.data(str, repr)
    def test_string_conversion(self, method):
        """
        Test conversion to string.
        """
        expected_str = '<Enterprise User 1234 in ee5e6b3a-069a-4947-bb8d-d2dbc323396c>'
        assert expected_str == method(self.user)
