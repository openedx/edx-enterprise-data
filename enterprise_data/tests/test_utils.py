"""
Test factories.
"""


from datetime import datetime

import factory
import pytz
from faker import Factory as FakerFactory
from faker.providers import misc

from django.contrib.auth import get_user_model

from enterprise_data.models import EnterpriseEnrollment, EnterpriseLearner, EnterpriseLearnerEnrollment, EnterpriseUser

FAKER = FakerFactory.create()
FAKER.add_provider(misc)
User = get_user_model()


class EnterpriseEnrollmentFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseCourseEnrollment factory.

    Creates an instance of EnterpriseCourseEnrollment with minimal boilerplate.
    """

    class Meta:
        """
        Meta for EnterpriseCourseEnrollmentFactory.
        """

        model = EnterpriseEnrollment

    id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1, max=999999))  # pylint: disable=no-member,invalid-name
    enterprise_id = str(FAKER.uuid4())  # pylint: disable=no-member
    lms_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    course_id = factory.lazy_attribute(lambda x: FAKER.slug())  # pylint: disable=no-member
    enrollment_created_timestamp = factory.lazy_attribute(lambda x: '2018-01-01T00:00:00Z')
    user_current_enrollment_mode = factory.lazy_attribute(lambda x: 'verified')
    has_passed = factory.lazy_attribute(lambda x: FAKER.boolean())  # pylint: disable=no-member
    consent_granted = True
    course_title = factory.lazy_attribute(lambda x: ' '.join(FAKER.words(nb=2)).title())  # pylint: disable=no-member
    course_start = factory.lazy_attribute(lambda x: FAKER.date_time_between(  # pylint: disable=no-member
        start_date='-2M',
        end_date='+2M',
        tzinfo=pytz.utc))
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    current_grade = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=0, max_value=1))  # pylint: disable=no-member

    @factory.lazy_attribute
    def course_end(self):
        return FAKER.date_time_between(   # pylint: disable=no-member
            start_date=self.course_start,
            end_date="+8M",
            tzinfo=pytz.utc)

    @factory.lazy_attribute
    def passed_timestamp(self):
        """ Create a passed timestamp if a course has been passed """
        if self.has_passed:
            return FAKER.date_time_between(  # pylint: disable=no-member
                start_date=self.course_start,
                end_date=self.course_end,
                tzinfo=pytz.utc)
        return None


class UserFactory(factory.django.DjangoModelFactory):
    """
    User Factory.

    Creates an instance of User with minimal boilerplate
    """
    class Meta:
        model = User
        django_get_or_create = ('email', 'username')

    _DEFAULT_PASSWORD = 'test'

    username = factory.Sequence('robot{}'.format)
    email = factory.Sequence('robot+test+{}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', _DEFAULT_PASSWORD)
    first_name = factory.Sequence('Robot{}'.format)
    last_name = 'Test'
    is_staff = factory.lazy_attribute(lambda x: False)
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1, tzinfo=pytz.utc)
    date_joined = datetime(2011, 1, 1, tzinfo=pytz.utc)


class EnterpriseUserFactory(factory.django.DjangoModelFactory):
    """
    Enterprise User Factory.

    Creates an instance of Enterprise User with minimal boilerplate
    """
    class Meta:
        model = EnterpriseUser

    enterprise_id = str(FAKER.uuid4())  # pylint: disable=no-member
    lms_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    enterprise_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    enterprise_sso_uid = factory.lazy_attribute(lambda x: FAKER.text(max_nb_chars=255))  # pylint: disable=no-member
    user_account_creation_timestamp = datetime(2011, 1, 1, tzinfo=pytz.utc)
    user_username = factory.Sequence('robot{}'.format)
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    user_country_code = factory.lazy_attribute(lambda x: FAKER.country_code())  # pylint: disable=no-member
    last_activity_date = datetime(2012, 1, 1).date()


class EnterpriseLearnerFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseLearner model Factory.
    """
    class Meta:
        model = EnterpriseLearner

    enterprise_user_id = factory.lazy_attribute(lambda x: FAKER.random_int(min=1))  # pylint: disable=no-member
    enterprise_customer_uuid = str(FAKER.uuid4())  # pylint: disable=no-member
    lms_user_created = datetime(2011, 1, 1, tzinfo=pytz.utc)
    user_username = factory.Sequence('robot{}'.format)
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    lms_user_country = factory.lazy_attribute(lambda x: FAKER.country_code())  # pylint: disable=no-member
    enterprise_sso_uid = factory.lazy_attribute(lambda x: FAKER.text(max_nb_chars=255))  # pylint: disable=no-member
    last_activity_date = datetime(2012, 1, 1).date()
    lms_user_id = factory.lazy_attribute(
        lambda x: FAKER.random_int(min=1, max=999999)  # pylint: disable=no-member
    )


class EnterpriseLearnerEnrollmentFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseLearnerEnrollment model factory.
    """

    class Meta:
        model = EnterpriseLearnerEnrollment

    enrollment_id = factory.lazy_attribute(
        lambda x: FAKER.random_int(min=1, max=999999)  # pylint: disable=no-member
    )
    enterprise_customer_uuid = str(FAKER.uuid4())  # pylint: disable=no-member
    courserun_key = factory.lazy_attribute(lambda x: FAKER.slug())  # pylint: disable=no-member
    enrollment_date = factory.lazy_attribute(lambda x: '2018-01-01')
    user_current_enrollment_mode = factory.lazy_attribute(lambda x: 'verified')
    has_passed = factory.lazy_attribute(lambda x: FAKER.boolean())  # pylint: disable=no-member
    is_consent_granted = factory.lazy_attribute(lambda x: FAKER.boolean())  # pylint: disable=no-member
    course_title = factory.lazy_attribute(lambda x: ' '.join(FAKER.words(nb=2)).title())  # pylint: disable=no-member
    course_start_date = factory.lazy_attribute(lambda x: FAKER.date_time_between(  # pylint: disable=no-member
        start_date='-2M',
        end_date='+2M',
        tzinfo=pytz.utc)
    )
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    current_grade = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=0, max_value=1)  # pylint: disable=no-member
    )

    @factory.lazy_attribute
    def course_end_date(self):
        return FAKER.date_time_between(   # pylint: disable=no-member
            start_date=self.course_start_date,
            end_date="+8M",
            tzinfo=pytz.utc
        )

    @factory.lazy_attribute
    def passed_date(self):
        """ Create a passed timestamp if a course has been passed """
        if self.has_passed:
            return FAKER.date_time_between(  # pylint: disable=no-member
                start_date=self.course_start_date,
                end_date=self.course_end_date,
                tzinfo=pytz.utc
            )
        return None


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
        'enable_audit_data_reporting': kwargs.get('enable_audit_data_reporting', False),
        'replace_sensitive_sso_username': False
    }
    return enterprise_api_dummy_data
