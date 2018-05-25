# -*- coding: utf-8 -*-
"""
Test factories.
"""

from datetime import datetime

import factory
from faker import Factory as FakerFactory

from django.contrib.auth.models import User

from enterprise_data.models import EnterpriseEnrollment

FAKER = FakerFactory.create()


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

    id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))
    enterprise_id = factory.lazy_attribute(lambda x: 'ee5e6b3a069a4947bb8dd2dbc323396c')
    lms_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))
    enterprise_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))
    course_id = factory.lazy_attribute(lambda x: FAKER.slug())
    enrollment_created_timestamp = factory.lazy_attribute(lambda x: '2018-01-01')
    user_current_enrollment_mode = factory.lazy_attribute(lambda x: 'verified')


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
