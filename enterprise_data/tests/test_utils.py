"""
Test factories.
"""


from datetime import datetime

import factory
import pytz
from faker import Factory as FakerFactory
from faker.providers import misc

from django.contrib.auth import get_user_model

from enterprise_data.models import (
    EnterpriseEnrollment,
    EnterpriseGroupMembership,
    EnterpriseLearner,
    EnterpriseLearnerEnrollment,
    EnterpriseOffer,
    EnterpriseSubsidyBudget,
    EnterpriseUser,
)

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
            return FAKER.date_time_between(   # pylint: disable=no-member
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
    enterprise_user_created = FAKER.past_datetime(start_date='-30d')
    enterprise_user_modified = FAKER.past_datetime(start_date='-30d')
    enterprise_user_active = FAKER.pybool()
    lms_user_id = factory.lazy_attribute(
        lambda x: FAKER.random_int(min=1, max=999999)  # pylint: disable=no-member
    )
    is_linked = FAKER.pybool()
    user_username = factory.Sequence('robot{}'.format)
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    lms_user_created = FAKER.past_datetime(start_date='-60d')
    lms_last_login = FAKER.past_datetime(start_date='-10d')
    lms_user_country = factory.lazy_attribute(lambda x: FAKER.country_code())  # pylint: disable=no-member
    enterprise_sso_uid = factory.lazy_attribute(lambda x: FAKER.text(max_nb_chars=255))  # pylint: disable=no-member
    last_activity_date = datetime(2012, 1, 1).date()
    created_at = FAKER.past_datetime(start_date='-30d')


class EnterpriseLearnerEnrollmentFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseLearnerEnrollment model factory.
    """

    class Meta:
        model = EnterpriseLearnerEnrollment

    enrollment_id = factory.lazy_attribute(
        lambda x: FAKER.random_int(min=1, max=999999)  # pylint: disable=no-member
    )
    enterprise_enrollment_id = factory.lazy_attribute(
        lambda x: FAKER.random_int(min=1, max=999999)  # pylint: disable=no-member
    )
    enterprise_customer_uuid = str(FAKER.uuid4())  # pylint: disable=no-member
    courserun_key = factory.lazy_attribute(lambda x: FAKER.slug())  # pylint: disable=no-member
    enrollment_date = factory.lazy_attribute(lambda x: '2018-01-01')
    user_current_enrollment_mode = factory.lazy_attribute(lambda x: 'verified')
    has_passed = factory.lazy_attribute(lambda x: FAKER.boolean())  # pylint: disable=no-member
    course_title = factory.lazy_attribute(lambda x: ' '.join(FAKER.words(nb=2)).title())  # pylint: disable=no-member
    course_start_date = factory.lazy_attribute(lambda x: FAKER.date_between(  # pylint: disable=no-member
        start_date='-2M',
        end_date='+2M',
    ))
    course_list_price = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(min_value=25.0, max_value=1000.0, right_digits=2)
    )
    current_grade = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=0, max_value=1)  # pylint: disable=no-member
    )
    letter_grade = factory.lazy_attribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    progress_status = factory.lazy_attribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    enterprise_user_id = factory.Sequence(lambda n: n)
    user_email = factory.lazy_attribute(lambda x: FAKER.email())  # pylint: disable=no-member
    user_username = factory.Sequence('robot{}'.format)
    user_first_name = factory.Sequence('Robot First {}'.format)
    user_last_name = factory.Sequence('Robot Last {}'.format)
    user_account_creation_date = factory.lazy_attribute(lambda x: '2018-01-01')
    user_country_code = factory.lazy_attribute(lambda x: FAKER.country_code())
    is_subsidy = factory.lazy_attribute(lambda x: FAKER.boolean())  # pylint: disable=no-member
    course_product_line = factory.LazyAttribute(lambda x: FAKER.pystr())

    @factory.lazy_attribute
    def course_end_date(self):
        return FAKER.date_between(   # pylint: disable=no-member
            start_date=self.course_start_date,
            end_date="+8M"
        )

    @factory.lazy_attribute
    def passed_date(self):
        """ Create a passed timestamp if a course has been passed """
        if self.has_passed and self.is_consent_granted:
            return FAKER.date_between(  # pylint: disable=no-member
                start_date=self.course_start_date,
                end_date=self.course_end_date,
            )
        return None

    @factory.lazy_attribute
    def last_activity_date(self):
        """ Create a date in between course start and end timestamp"""
        if self.is_consent_granted:
            return FAKER.date_between(  # pylint: disable=no-member
                start_date=self.course_start_date,
                end_date=self.course_end_date,
            )
        return None

    @factory.post_generation
    def set_fields_according_to_consent(
            obj,
            create,
            extracted,
            **kwargs
    ):  # pylint: disable=unused-argument, missing-function-docstring
        dsc_dependent_fields = [
            'last_activity_date',
            'progress_status',
            'passed_date',
            'current_grade',
            'letter_grade',
            'enterprise_user_id',
            'user_email',
            'user_account_creation_date',
            'user_country_code',
            'user_username',
            'user_first_name',
            'user_last_name',
        ]
        if create and not obj.is_consent_granted:
            for field in dsc_dependent_fields:
                setattr(obj, field, None)
            obj.save()


class EnterpriseSubsidyBudgetFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseSubsidyBudget model Factory.
    """
    class Meta:
        model = EnterpriseSubsidyBudget

    id = factory.LazyAttribute(lambda x: FAKER.uuid4().replace('-', ''))
    subsidy_access_policy_uuid = factory.LazyAttribute(lambda x: FAKER.uuid4().replace('-', ''))
    subsidy_uuid = factory.LazyAttribute(lambda x: FAKER.uuid4().replace('-', ''))
    enterprise_customer_uuid = factory.LazyAttribute(lambda x: FAKER.uuid4().replace('-', ''))
    enterprise_customer_name = factory.LazyAttribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    subsidy_access_policy_description = factory.LazyAttribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    subsidy_title = factory.LazyAttribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    catalog_name = factory.LazyAttribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    subsidy_access_policy_type = 'PerLearnerSpendCreditAccessPolicy'
    date_created = factory.LazyAttribute(lambda _: datetime(2020, 1, 1, tzinfo=pytz.utc))
    subsidy_start_datetime = factory.LazyAttribute(lambda _: datetime(2022, 1, 1, tzinfo=pytz.utc))
    subsidy_expiration_datetime = factory.LazyAttribute(lambda _: datetime(2090, 1, 1, tzinfo=pytz.utc))
    is_active = True
    is_test = False
    ocm_usage = factory.lazy_attribute(
        lambda x: round(x.amount_of_policy_spent / 2, 2)
    )
    exec_ed_usage = factory.lazy_attribute(
        lambda x: round(x.amount_of_policy_spent / 2, 2)
    )
    usage_total = factory.lazy_attribute(
        lambda x: x.amount_of_policy_spent
    )
    enterprise_contract_discount_percent = factory.LazyAttribute(
        lambda _: FAKER.pyfloat(right_digits=2, min_value=1, max_value=100)
    )
    starting_balance = factory.LazyAttribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=10000, max_value=100000)
    )
    amount_of_policy_spent = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=1, max_value=x.starting_balance)
    )
    remaining_balance = factory.lazy_attribute(
        lambda x: x.starting_balance - x.amount_of_policy_spent
    )
    percent_of_policy_spent = factory.lazy_attribute(
        lambda x: round(x.amount_of_policy_spent / x.starting_balance, 2)
    )


class EnterpriseGroupMembershipFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseGroupMembership model Factory.
    """
    class Meta:
        model = EnterpriseGroupMembership

    enterprise_customer_id = factory.LazyAttribute(lambda _: FAKER.uuid4())
    enterprise_group_name = factory.LazyAttribute(lambda _: ' '.join(FAKER.words(nb=2)).title())
    enterprise_group_uuid = factory.LazyAttribute(lambda _: FAKER.uuid4())
    group_is_removed = factory.LazyAttribute(lambda _: FAKER.boolean())
    group_type = factory.LazyAttribute(lambda _: 'budget')
    activated_at = factory.LazyAttribute(lambda _: FAKER.date_time_this_decade(tzinfo=pytz.UTC))
    enterprise_customer_user_id = factory.LazyAttribute(lambda _: FAKER.random_int(min=1, max=10000))
    membership_is_removed = factory.LazyAttribute(lambda _: FAKER.boolean())
    membership_status = factory.LazyAttribute(lambda _: FAKER.word())
    enterprise_group_membership_uuid = factory.LazyAttribute(lambda _: FAKER.uuid4())

    is_applies_to_all_contexts = factory.LazyAttribute(lambda _: FAKER.boolean())


class EnterpriseOfferFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseLearner model Factory.
    """
    class Meta:
        model = EnterpriseOffer

    offer_id = factory.LazyAttribute(lambda x: FAKER.pystr(min_chars=36, max_chars=200))
    enterprise_customer_uuid = factory.LazyAttribute(lambda x: FAKER.uuid4().replace('-', ''))
    enterprise_name = factory.LazyAttribute(lambda x: ' '.join(FAKER.words(nb=2)).title())
    max_discount = factory.LazyAttribute(lambda x: FAKER.pyfloat(right_digits=2, min_value=10000, max_value=100000))
    sum_course_price = factory.lazy_attribute(
        lambda x: FAKER.pyfloat(right_digits=2, min_value=1, max_value=x.max_discount)
    )
    status = 'Open'
    offer_type = 'Site'
    date_created = factory.LazyAttribute(lambda _: datetime(2012, 1, 1, tzinfo=pytz.utc))
    discount_type = 'Percentage'
    discount_value = factory.LazyAttribute(lambda _: FAKER.pyfloat(right_digits=2, min_value=1, max_value=100))
    total_discount_ecommerce = factory.lazy_attribute(
        lambda x: round(x.sum_course_price * (x.discount_value / 100), 2)
    )
    amount_of_offer_spent = factory.lazy_attribute(
        lambda x: x.total_discount_ecommerce
    )
    sum_amount_learner_paid = factory.lazy_attribute(
        lambda x: x.sum_course_price - x.amount_of_offer_spent
    )
    percent_of_offer_spent = factory.lazy_attribute(
        lambda x: round(x.amount_of_offer_spent / x.max_discount, 2)
    )
    remaining_balance = factory.lazy_attribute(
        lambda x: round(x.max_discount - x.amount_of_offer_spent, 2)
    )
    amount_offer_spent_ocm = factory.lazy_attribute(
        lambda x: round(x.amount_of_offer_spent / 2, 2)
    )
    amount_offer_spent_exec_ed = factory.lazy_attribute(
        lambda x: round(x.amount_of_offer_spent / 2, 2)
    )


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


def get_dummy_engagements_data(enterprise_uuid: str, count=10):
    """
    Utility method to get dummy enrollment's data.
    """
    return [
        {
            'user_id': FAKER.random_int(min=1),
            'email': FAKER.email(),
            'enterprise_customer_uuid': enterprise_uuid,
            'course_key': FAKER.slug(),
            'enroll_type': 'verified',
            'activity_date': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'course_title': ' '.join(FAKER.words(nb=5)).title(),
            'course_subject': ' '.join(FAKER.words(nb=2)).title(),
            'is_engaged': FAKER.boolean(),
            'is_engaged_video': FAKER.boolean(),
            'is_engaged_forum': FAKER.boolean(),
            'is_engaged_problem': FAKER.boolean(),
            'is_active': FAKER.boolean(),
            'learning_time_seconds': FAKER.random_int(min=1),
        } for _ in range(count)
    ]


def get_dummy_enrollments_data(enterprise_uuid: str, count=10):
    """
    Utility method to get dummy enrollment's data.
    """
    return [
        {
            'enterprise_customer_name': ' '.join(FAKER.words(nb=2)).title(),
            'enterprise_customer_uuid': enterprise_uuid,
            'lms_enrollment_id': FAKER.random_int(min=1),
            'user_id': FAKER.random_int(min=1),
            'email': FAKER.email(),
            'course_key': FAKER.slug(),
            'courserun_key': FAKER.slug(),
            'course_id': FAKER.slug(),
            'course_subject': ' '.join(FAKER.words(nb=2)).title(),
            'course_title': ' '.join(FAKER.words(nb=5)).title(),
            'enterprise_enrollment_date': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'lms_enrollment_mode': 'verified',
            'enroll_type': 'verified',
            'program_title': ' '.join(FAKER.words(nb=2)).title(),
            'date_certificate_awarded': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'grade_percent': FAKER.pyfloat(right_digits=2, min_value=0, max_value=1),
            'cert_awarded': FAKER.boolean(),
            'date_certificate_created_raw': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'passed_date_raw': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'passed_date': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'has_passed': FAKER.boolean(),
        } for _ in range(count)
    ]


def get_dummy_skills_data(enterprise_uuid: str, count=10):
    """
    Utility method to get dummy skills data.
    """
    return [
        {
            'course_number': FAKER.random_int(min=1),
            'skill_type': 'skill_type',
            'skill_name': ' '.join(FAKER.words(nb=2)).title(),
            'skill_url': FAKER.url(),
            'confidence': FAKER.random_int(min=1),
            'skill_rank': FAKER.random_int(min=1),
            'course_title': ' '.join(FAKER.words(nb=5)).title(),
            'course_key': FAKER.slug(),
            'level_type': 'level_type',
            'primary_subject_name': ' '.join(FAKER.words(nb=2)).title(),
            'date': FAKER.date_time_between(
                start_date='-2M',
                end_date='+2M',
            ),
            'enterprise_customer_uuid': enterprise_uuid,
            'enterprise_customer_name': ' '.join(FAKER.words(nb=2)).title(),
            'enrolls': FAKER.random_int(min=1),
            'completions': FAKER.random_int(min=1),
        } for _ in range(count)
    ]
