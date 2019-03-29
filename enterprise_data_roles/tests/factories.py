# -*- coding: utf-8 -*-
"""
Test factories.
"""
from __future__ import absolute_import, unicode_literals

import factory
from faker import Factory as FakerFactory
from faker.providers import misc

from enterprise_data.tests.test_utils import UserFactory
from enterprise_data_roles.models import EnterpriseDataFeatureRole, EnterpriseDataRoleAssignment

FAKER = FakerFactory.create()
FAKER.add_provider(misc)


class EnterpriseDataFeatureRoleFactory(factory.django.DjangoModelFactory):
    """
    Enterprise Data Feature Role Factory.

    Creates an instance of EnterpriseDataFeatureRole with minimal boilerplate
    """
    class Meta(object):
        model = EnterpriseDataFeatureRole

    name = factory.Sequence(u'User Role-{0}'.format)
    description = factory.lazy_attribute(lambda x: FAKER.text(max_nb_chars=255))  # pylint: disable=no-member


class EnterpriseDataRoleAssignmentFactory(factory.django.DjangoModelFactory):
    """
    Enterprise Data Role Assignment Factory.

    Creates an instance of EnterpriseDataRoleAssignment with minimal boilerplate
    """
    class Meta(object):
        model = EnterpriseDataRoleAssignment

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(EnterpriseDataFeatureRoleFactory)
