# -*- coding: utf-8 -*-
"""
Test factories.
"""
from __future__ import absolute_import, unicode_literals

from datetime import datetime

import factory
from faker import Factory as FakerFactory
from faker.providers import misc

from django.contrib.auth.models import User

from enterprise_data.models import EnterpriseEnrollment, EnterpriseUser

FAKER = FakerFactory.create()
FAKER.add_provider(misc)


class EnterpriseEnrollmentFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseCourseEnrollment factory.

    Creates an instance of EnterpriseCourseEnrollment with minimal boilerplate.
    """

    class Meta(object):
        """
        Meta for EnterpriseCourseEnrollmentFactory.
        """

        model = EnterpriseEnrollment

    id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1, max=999999))  # pylint: disable=no-member,invalid-name
    enterprise_id = str(FAKER.uuid4())  # pylint: disable=no-member
    lms_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    course_id = factory.lazy_attribute(lambda x: FAKER.slug())  # pylint: disable=no-member
    enrollment_created_timestamp = factory.lazy_attribute(lambda x: '2018-01-01')
    user_current_enrollment_mode = factory.lazy_attribute(lambda x: 'verified')
    has_passed = False


class UserFactory(factory.django.DjangoModelFactory):
    """
    User Factory.

    Creates an instance of User with minimal boilerplate
    """
    class Meta(object):
        model = User
        django_get_or_create = ('email', 'username')

    _DEFAULT_PASSWORD = 'test'

    username = factory.Sequence(u'robot{0}'.format)
    email = factory.Sequence(u'robot+test+{0}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', _DEFAULT_PASSWORD)
    first_name = factory.Sequence(u'Robot{0}'.format)
    last_name = 'Test'
    is_staff = factory.lazy_attribute(lambda x: False)
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1)
    date_joined = datetime(2011, 1, 1)


class EnterpriseUserFactory(factory.django.DjangoModelFactory):
    """
    Enterprise User Factory.

    Creates an instance of Enterprise User with minimal boilerplate
    """
    class Meta(object):
        model = EnterpriseUser

    enterprise_id = str(FAKER.uuid4())  # pylint: disable=no-member
    lms_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    enterprise_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    enterprise_sso_uid = factory.lazy_attribute(lambda x: FAKER.text(max_nb_chars=255))  # pylint: disable=no-member
    user_account_creation_timestamp = datetime(2011, 1, 1)
    user_username = factory.Sequence(u'robot{0}'.format)
    user_email = factory.Sequence(u'robot+test+{0}@edx.org'.format)
    user_country_code = factory.lazy_attribute(lambda x: FAKER.country_code())  # pylint: disable=no-member
    last_activity_date = datetime(2012, 1, 1).date()


def get_dummy_enterprise_api_data(**kwargs):
    """
    DRY method to get enterprise dummy data.

    Get dummy data for an enterprise from `enterprise-customer` API.
    """
    enterprise_api_dummy_data = {
        'uuid': kwargs.get('enterprise_id', 'ee5e6b3a-069a-4947-bb8d-d2dbc323396c'),
        'name': 'Enterprise ABC',
        'slug': 'enterprise_abc',
        'active': True,
        'enable_data_sharing_consent': kwargs.get('enable_data_sharing_consent', True),
        'enforce_data_sharing_consent': kwargs.get('enforce_data_sharing_consent', 'at_enrollment'),
        'branding_configuration': {},
        'identity_provider': 'saml-ubc',
        'enable_audit_enrollment': kwargs.get('enable_audit_enrollment', False),
        'replace_sensitive_sso_username': False
    }
    return enterprise_api_dummy_data
