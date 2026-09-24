"""
Test factories.
"""

from datetime import datetime, timedelta

import factory
from factory.faker import Faker
from faker import Factory as FakerFactory
from faker.providers import misc

from enterprise_data.models import EnterpriseAdminLearnerProgress, EnterpriseAdminSummarizeInsights

FAKER = FakerFactory.create()
FAKER.add_provider(misc)


class EnterpriseAdminLearnerProgressFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseAdminLearnerProgress Factory.
    """
    class Meta:
        model = EnterpriseAdminLearnerProgress

    enterprise_customer_uuid = Faker('uuid4')
    enterprise_customer_name = FAKER.company()
    active_subscription_plan = True
    assigned_licenses = FAKER.pyint(min_value=0)
    activated_licenses = FAKER.pyint(min_value=0)
    assigned_licenses_percentage = FAKER.pyfloat(min_value=0.0, max_value=100)
    activated_licenses_percentage = FAKER.pyfloat(min_value=0.0, max_value=100)
    active_enrollments = FAKER.pyint(min_value=0)
    at_risk_enrollment_less_than_one_hour = FAKER.pyint(min_value=0)
    at_risk_enrollment_end_date_soon = FAKER.pyint(min_value=0)
    at_risk_enrollment_dormant = FAKER.pyint(min_value=0)
    created_at = datetime.now()


class EnterpriseAdminSummarizeInsightsFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseAdminSummarizeInsights Factory.
    """
    class Meta:
        model = EnterpriseAdminSummarizeInsights

    enterprise_customer_uuid = Faker('uuid4')
    enterprise_customer_name = FAKER.company()
    enrolls = FAKER.pyint(min_value=0)
    enrolls_prior = FAKER.pyint(min_value=0)
    passed = FAKER.pyint(min_value=0)
    passed_prior = FAKER.pyint(min_value=0)
    engage = FAKER.pyint(min_value=0)
    engage_prior = FAKER.pyint(min_value=0)
    hours = FAKER.pyint(min_value=0)
    hours_prior = FAKER.pyint(min_value=0)
    contract_end_date = datetime.now() + timedelta(days=30)
    active_contract = True
    created_at = datetime.now()
