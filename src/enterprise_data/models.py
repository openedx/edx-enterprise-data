"""
Database models for enterprise data.
"""


from logging import getLogger

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from enterprise_data.utils import get_unique_id

LOGGER = getLogger(__name__)


class EnterpriseReportingModelManager(models.Manager):
    """
    Custom ModelManager for every model that wants to use `enterprise_reporting` database.
    """

    def get_queryset(self):
        """
        Override to use the `enterprise_reporting` database instead of default.
        """
        qs = super().get_queryset()
        qs = qs.using(settings.ENTERPRISE_REPORTING_DB_ALIAS)

        return qs


class EnterpriseLearner(models.Model):
    """
    Information related to Enterprise Learner.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_learner'
        verbose_name = _("Enterprise Learner")
        verbose_name_plural = _("Enterprise Learner")
        ordering = ['-user_email']

    enterprise_user_id = models.PositiveIntegerField(primary_key=True)
    enterprise_customer_uuid = models.UUIDField(db_index=True, null=False)
    enterprise_user_created = models.DateTimeField(null=True)
    enterprise_user_modified = models.DateTimeField(null=True)
    enterprise_user_active = models.BooleanField(default=False)
    lms_user_id = models.PositiveIntegerField()
    is_linked = models.BooleanField(default=False)
    user_username = models.CharField(max_length=255, null=True)
    user_email = models.CharField(max_length=255, null=True, db_index=True)
    lms_user_created = models.DateTimeField(null=True)
    lms_last_login = models.DateTimeField(null=True)
    lms_user_country = models.CharField(max_length=2, null=True)
    enterprise_sso_uid = models.CharField(max_length=255, null=True)
    last_activity_date = models.DateField(null=True, db_index=True)
    created_at = models.DateTimeField(null=True, db_index=True)


class EnterpriseLearnerEnrollment(models.Model):
    """
    Information related to Enterprise Learner Enrollments.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_learner_enrollment'
        verbose_name = _("Enterprise Learner Enrollment")
        verbose_name_plural = _("Enterprise Learner Enrollments")
        indexes = [
            models.Index(fields=['enterprise_customer_uuid', 'enterprise_user_id', 'user_current_enrollment_mode']),
            models.Index(fields=['enterprise_customer_uuid', 'offer_id', 'budget_id']),
            models.Index(fields=[
                'enterprise_customer_uuid', 'user_current_enrollment_mode', 'coupon_code', 'offer_type'
            ]),
        ]

    enterprise_enrollment_id = models.PositiveIntegerField(null=True)
    enrollment_id = models.PositiveIntegerField(null=True)
    is_consent_granted = models.BooleanField(default=False)
    paid_by = models.CharField(max_length=255, null=True)
    user_current_enrollment_mode = models.CharField(max_length=32)
    enrollment_date = models.DateField()
    unenrollment_date = models.DateField(null=True)
    unenrollment_end_within_date = models.DateField(null=True)
    is_refunded = models.BooleanField(default=None, null=True)
    seat_delivery_method = models.CharField(max_length=255, null=True)
    offer_id = models.CharField(max_length=255, null=True)
    offer_name = models.CharField(max_length=255, null=True)
    offer_type = models.CharField(max_length=255, null=True)
    coupon_code = models.CharField(max_length=255, null=True)
    coupon_name = models.CharField(max_length=255, null=True)
    contract_id = models.CharField(max_length=255, null=True)
    course_list_price = models.FloatField(null=True)
    amount_learner_paid = models.FloatField(null=True)
    course_key = models.CharField(max_length=255, null=False, db_index=True)
    courserun_key = models.CharField(max_length=255, null=False, db_index=True)
    course_title = models.CharField(max_length=255, null=True, db_index=True)
    course_pacing_type = models.CharField(max_length=32, null=True)
    course_start_date = models.DateField(null=True, db_index=True)
    course_end_date = models.DateField(null=True)
    course_duration_weeks = models.PositiveIntegerField(null=True)
    course_max_effort = models.PositiveIntegerField(null=True)
    course_min_effort = models.PositiveIntegerField(null=True)
    course_primary_program = models.CharField(max_length=255, null=True)
    primary_program_type = models.CharField(max_length=255, null=True)
    course_primary_subject = models.CharField(max_length=255, null=True)
    has_passed = models.BooleanField(default=False)
    last_activity_date = models.DateField(null=True, db_index=True)
    total_learning_time_seconds = models.PositiveIntegerField(default=0)
    progress_status = models.CharField(max_length=255, null=True)
    passed_date = models.DateField(null=True)
    current_grade = models.FloatField(null=True)
    letter_grade = models.CharField(max_length=64, null=True)
    enterprise_user = models.ForeignKey(
        'EnterpriseLearner',
        related_name='enrollments',
        to_field='enterprise_user_id',
        on_delete=models.CASCADE,
        null=True,
    )
    user_email = models.CharField(max_length=255, null=True, db_index=True)
    user_account_creation_date = models.DateTimeField(null=True)
    user_country_code = models.CharField(max_length=2, null=True)
    user_username = models.CharField(max_length=255, null=True)
    user_first_name = models.CharField(max_length=255, null=True)
    user_last_name = models.CharField(max_length=255, null=True)
    enterprise_name = models.CharField(max_length=255, db_index=True, null=False)
    enterprise_customer_uuid = models.UUIDField(db_index=True, null=False)
    enterprise_sso_uid = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(null=True, db_index=True)
    is_subsidy = models.BooleanField(default=False)
    course_product_line = models.CharField(max_length=64, null=True)
    budget_id = models.UUIDField(db_index=True, null=True)
    is_included_in_utilization = models.BooleanField(default=False)
    lpr_unique_id = models.PositiveBigIntegerField(primary_key=True, default=get_unique_id)
    subscription_license_uuid = models.UUIDField(null=True)
    enterprise_group_name = models.CharField(max_length=25, null=True)
    enterprise_group_uuid = models.UUIDField(null=True)


class EnterpriseAdminLearnerProgress(models.Model):
    """
    Aggregated data on learners at different risk points, either during subsidy activation or throughout the course.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_admin_learner_progress'
        verbose_name = _("Enterprise Admin Learner Progress")
        verbose_name_plural = _("Enterprise Admin Learner Progress")

    enterprise_customer_uuid = models.UUIDField(primary_key=True)
    enterprise_customer_name = models.CharField(max_length=255)
    active_subscription_plan = models.BooleanField(
        help_text='Whether the subscription plan is active or nor?'
    )
    assigned_licenses = models.PositiveIntegerField(
        help_text='Number of assigned licenses'
    )
    activated_licenses = models.PositiveIntegerField(
        help_text='Number of active licenses'
    )
    assigned_licenses_percentage = models.FloatField(
        help_text='Float representation of percentage of assigned licenses out of total'
    )
    activated_licenses_percentage = models.FloatField(
        help_text='Float representation of percentage of active licenses out of total'
    )
    active_enrollments = models.PositiveIntegerField(
        help_text='Number of enrollments in active courses'
    )
    at_risk_enrollment_less_than_one_hour = models.PositiveIntegerField(
        help_text='Number of enrollments from the past 30 days that have not yet achieved 1 hour of learning time'
    )
    at_risk_enrollment_end_date_soon = models.PositiveIntegerField(
        help_text=(
            'Number of enrollments have end dates coming up in the next 30 days. Course complete time is almost up'
        )
    )
    at_risk_enrollment_dormant = models.PositiveIntegerField(
        help_text='Number of dormant enrollments in the past 30 days'
    )
    created_at = models.DateTimeField()


class EnterpriseAdminSummarizeInsights(models.Model):
    """
    Aggregated data on enrollments, daily sessions, learning hours, and completions for the past 60 days.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_admin_summarize_insights'
        verbose_name = _("Enterprise Admin Summarize Insights")
        verbose_name_plural = _("Enterprise Admin Summarize Insights")

    enterprise_customer_uuid = models.UUIDField(primary_key=True)
    enterprise_customer_name = models.CharField(max_length=255)
    enrolls = models.PositiveIntegerField(help_text='Total number of enrollments in last 30 days')
    enrolls_prior = models.PositiveIntegerField(help_text='Total number of enrollments in last 31-60 days')
    passed = models.PositiveIntegerField(help_text='Total number of completions in last 30 days')
    passed_prior = models.PositiveIntegerField(help_text='Total number of completions in last 31-60 days')
    engage = models.PositiveIntegerField(help_text='Total number of daily sessions/engagements in last 30 days')
    engage_prior = models.PositiveIntegerField(
        help_text='Total number of daily sessions/engagements in last 31-60 days'
    )
    hours = models.PositiveIntegerField(help_text='Total number of learning hours in last 30 days')
    hours_prior = models.PositiveIntegerField(help_text='Total number of learning hours in last 31-60 days')
    contract_end_date = models.DateTimeField(help_text='Contract end date')
    active_contract = models.BooleanField(help_text='Whether or not the customer has a contract?')
    created_at = models.DateTimeField()


class EnterpriseEnrollment(models.Model):
    """Enterprise Enrollment is the learner details for a specific course enrollment.

    This information includes a mix of the learners meta data (email, username, etc), the enterprise they are
    associated with (enterprise_id, enterprise_name, etc), and their status in the course (course_id,
    letter_grade, has_passed, etc).
    This is meant to closely mirror the data the Enterprises recieve in the automated report (see enterprise_reporting
    folder in this repo), with the exception of some data that is only calculated in Vertica as this data is pulled from
    the analytics result store via the analytics-data-api project.
    """

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_enrollment'
        verbose_name = _("Enterprise Enrollment")
        verbose_name_plural = _("Enterprise Enrollments")

    enterprise_id = models.UUIDField()
    enterprise_name = models.CharField(max_length=255)
    lms_user_id = models.PositiveIntegerField()
    enterprise_user = models.ForeignKey(
        'EnterpriseUser',
        related_name='enrollments',
        to_field='enterprise_user_id',
        on_delete=models.CASCADE,
    )
    course_id = models.CharField(max_length=255, help_text='The course the learner is enrolled in.')
    enrollment_created_timestamp = models.DateTimeField()
    user_current_enrollment_mode = models.CharField(max_length=32)
    consent_granted = models.BooleanField(default=None, null=True)
    letter_grade = models.CharField(max_length=32, null=True)
    has_passed = models.BooleanField(default=False)
    passed_timestamp = models.DateTimeField(null=True)
    enterprise_sso_uid = models.CharField(max_length=255, null=True)
    enterprise_site_id = models.PositiveIntegerField(null=True)
    course_title = models.CharField(max_length=255, null=True)
    course_start = models.DateTimeField(null=True)
    course_end = models.DateTimeField(null=True)
    course_pacing_type = models.CharField(max_length=32, null=True)
    course_duration_weeks = models.CharField(max_length=32, null=True)
    course_min_effort = models.PositiveIntegerField(null=True)
    course_max_effort = models.PositiveIntegerField(null=True)
    user_account_creation_timestamp = models.DateTimeField(null=True)
    user_email = models.CharField(max_length=255, null=True)
    user_username = models.CharField(max_length=255, null=True)
    course_key = models.CharField(max_length=255, null=True)
    user_country_code = models.CharField(max_length=2, null=True)
    last_activity_date = models.DateField(null=True)
    coupon_name = models.CharField(max_length=128, null=True)
    coupon_code = models.CharField(max_length=128, null=True)
    offer = models.CharField(max_length=128, null=True)
    current_grade = models.FloatField(null=True)
    course_price = models.DecimalField(decimal_places=2, max_digits=12, null=True)
    discount_price = models.DecimalField(decimal_places=2, max_digits=12, null=True)
    created = models.DateTimeField(null=True)
    unenrollment_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return "<Enterprise Enrollment for user {user} in {course}>".format(
            user=self.enterprise_user_id,
            course=self.course_id
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseOffer(models.Model):
    """
    Details for an enterprise offer.

    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_offer_aggregates'
        verbose_name = _("Enterprise Offer")
        verbose_name_plural = _("Enterprise Offers")

    offer_id = models.CharField(max_length=255, primary_key=True)
    enterprise_customer_uuid = models.UUIDField()
    enterprise_name = models.CharField(max_length=255, null=True)
    sum_amount_learner_paid = models.FloatField(null=True)
    sum_course_price = models.FloatField(null=True)
    status = models.CharField(max_length=255, null=True)
    offer_type = models.CharField(max_length=255, null=True)
    date_created = models.DateTimeField(null=True)
    emails_for_usage_alert = models.CharField(max_length=1023, null=True)
    discount_type = models.CharField(max_length=64, null=True)
    discount_value = models.FloatField(null=True)
    max_discount = models.FloatField(null=True)
    total_discount_ecommerce = models.FloatField(null=True)
    amount_of_offer_spent = models.FloatField(null=True)
    percent_of_offer_spent = models.FloatField(null=True)
    remaining_balance = models.FloatField(null=True)
    amount_offer_spent_ocm = models.FloatField(null=True)
    amount_offer_spent_exec_ed = models.FloatField(null=True)
    export_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return f'<Enterprise Offer {self.offer_id} for {self.enterprise_name}>'

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseSubsidyBudget(models.Model):
    """
    Details for budgets in an enterprise offer.

    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'ent_subsidy_access_policy_aggregates'
        verbose_name = _("Enterprise Subsidy Budget")
        verbose_name_plural = _("Enterprise Subsidy Budgets")

    id = models.CharField(
        db_index=True,
        primary_key=True,
        max_length=32,
        help_text="Hashed surrogate key based on subsidy_access_policy_uuid and subsidy_uuid"
    )
    subsidy_access_policy_uuid = models.UUIDField(help_text="Budget Id")
    subsidy_uuid = models.UUIDField()
    enterprise_customer_uuid = models.UUIDField()
    enterprise_customer_name = models.CharField(max_length=255, null=True)
    subsidy_access_policy_description = models.CharField(max_length=500, null=True)
    subsidy_access_policy_display_name = models.CharField(max_length=512, null=True)
    subsidy_title = models.CharField(max_length=255, null=True)
    catalog_name = models.CharField(max_length=255, null=True)
    subsidy_access_policy_type = models.CharField(max_length=255, null=True)
    date_created = models.DateTimeField(null=True)
    subsidy_start_datetime = models.DateTimeField(null=True)
    subsidy_expiration_datetime = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=False)
    is_test = models.BooleanField(default=False)
    ocm_usage = models.FloatField(null=True)
    exec_ed_usage = models.FloatField(null=True)
    usage_total = models.FloatField(null=True)
    enterprise_contract_discount_percent = models.FloatField(null=True)
    starting_balance = models.FloatField(null=True)
    amount_of_policy_spent = models.FloatField(null=True)
    remaining_balance = models.FloatField(null=True)
    percent_of_policy_spent = models.FloatField(null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return (f'<Enterprise Budget {self.subsidy_access_policy_uuid} for '
                f'Subsidy {self.subsidy_uuid} for {self.enterprise_customer_name}>')

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseGroupMembership(models.Model):
    """
    Details of group memberships in enterprise reports.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'group_membership'
        verbose_name = _("Group Membership")
        verbose_name_plural = _("Group Memberships")
        indexes = [
            models.Index(fields=['enterprise_group_uuid', 'group_type', 'enterprise_customer_user_id']),
        ]

    group_membership_unique_id = models.CharField(max_length=64, primary_key=True)
    is_applies_to_all_contexts = models.BooleanField(default=False)
    enterprise_customer_id = models.UUIDField(db_index=True, null=True)
    enterprise_group_name = models.CharField(max_length=255, null=True)
    enterprise_group_uuid = models.UUIDField(null=True)
    group_is_removed = models.BooleanField(default=False)
    group_type = models.CharField(max_length=128, null=True)
    activated_at = models.DateTimeField(null=True)
    enterprise_customer_user_id = models.PositiveIntegerField(null=True)
    membership_is_removed = models.BooleanField(default=False)
    membership_status = models.CharField(max_length=128, null=True)
    enterprise_group_membership_uuid = models.UUIDField(null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return (f'<Enterprise Group Membership: {self.enterprise_group_name} '
                f'(Group UUID: {self.enterprise_group_uuid}) '
                f'for Customer ID {self.enterprise_customer_id}>')

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseUser(models.Model):
    """Information includes a mix of the user's meta data.

    Includes (lms_user_id, username, etc), and the enterprise they are associated with (enterprise_id).
    """

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_user'
        verbose_name = _("Enterprise User")
        verbose_name_plural = _("Enterprise Users")
        ordering = ['-user_email']

    enterprise_id = models.UUIDField()
    lms_user_id = models.PositiveIntegerField()
    enterprise_user_id = models.PositiveIntegerField(unique=True)
    enterprise_sso_uid = models.CharField(max_length=255, null=True)
    user_account_creation_timestamp = models.DateTimeField(null=True)
    user_email = models.CharField(max_length=255, null=True)
    user_username = models.CharField(max_length=255, null=True)
    user_country_code = models.CharField(max_length=2, null=True)
    last_activity_date = models.DateField(null=True)
    created = models.DateTimeField(null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return "<Enterprise User {user} in {enterprise}>".format(
            user=self.lms_user_id,
            enterprise=self.enterprise_id
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()


class EnterpriseExecEdLCModulePerformance(models.Model):
    """
    Model for  Exec Ed LC Module Performance.
    """

    objects = EnterpriseReportingModelManager()

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'exec_ed_lc_module_performance'
        verbose_name = _("Exec Ed LC Module Performance")
        verbose_name_plural = _("Exec Ed LC Module Performance")

    module_performance_unique_id = models.CharField(max_length=350, primary_key=True)
    registration_id = models.PositiveIntegerField(null=True)
    subsidy_transaction_id = models.UUIDField(null=True)
    enterprise_customer_uuid = models.UUIDField(db_index=True, null=True)
    ocm_lms_user_id = models.PositiveIntegerField(null=True)
    is_internal_subsidy = models.BooleanField(null=True)
    ocm_enrollment_id = models.PositiveIntegerField(null=True)
    ocm_courserun_key = models.CharField(max_length=255, null=True)
    university_name = models.CharField(max_length=500, null=True)
    university_abbreviation = models.CharField(max_length=255, null=True)
    partner_short_name = models.CharField(max_length=255, null=True)
    university_country = models.CharField(max_length=255, null=True)
    school = models.CharField(max_length=500, null=True)
    faculty = models.CharField(max_length=500, null=True)
    department = models.CharField(max_length=500, null=True)
    course_code = models.PositiveIntegerField(null=True)
    course_name = models.CharField(max_length=500, db_index=True)
    course_abbreviation = models.CharField(max_length=128, null=True)
    course_abbreviation_short = models.CharField(max_length=64, null=True)
    course_type = models.CharField(max_length=128, null=True)
    subject_vertical = models.CharField(max_length=128, null=True)
    presentation_abbreviation = models.CharField(max_length=128, null=True)
    presentation_name = models.CharField(max_length=500, null=True)
    presentation_code = models.PositiveIntegerField(null=True)
    presentation_close_date = models.DateField(null=True)
    presentation_start_date = models.DateField(null=True)
    promotion_code = models.CharField(max_length=255, null=True)
    promotion_category_name = models.CharField(max_length=255, null=True)
    product_type = models.CharField(max_length=128, null=True)
    product_life_cycle_status = models.CharField(max_length=128, null=True)
    enrolment_id = models.PositiveIntegerField(null=True)
    olc_user_id = models.PositiveIntegerField(null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=128, null=True)
    company_name = models.CharField(max_length=255, null=True)
    module_number = models.PositiveIntegerField(null=True)
    module_name = models.CharField(max_length=255, null=True)
    module_1_release_date = models.DateField(null=True)
    last_module_release_date = models.DateField(null=True)
    last_module_end_date = models.DateField(null=True)
    final_mark = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    assign_grade = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    last_access = models.DateField(null=True)
    all_activities_completed_count = models.PositiveIntegerField(null=True)
    all_activities_total_count = models.PositiveIntegerField(null=True)
    percentage_completed_activities = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    extensions_requested = models.PositiveIntegerField(null=True)
    module_grade = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    log_viewed = models.PositiveIntegerField(null=True)
    hours_online = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    orientation_module_accessed = models.CharField(max_length=128, null=True)
    graded_activities_completed_count = models.PositiveIntegerField(null=True)
    graded_activities_total_count = models.PositiveIntegerField(null=True)
    percentage_completed_graded_activities = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    assessment_activities_completed_count = models.PositiveIntegerField(null=True)
    assessment_activities_total_count = models.PositiveIntegerField(null=True)
    course_material_activities_completed_count = models.PositiveIntegerField(null=True)
    course_material_activities_total_count = models.PositiveIntegerField(null=True)
    discussion_forum_activities_completed_count = models.PositiveIntegerField(null=True)
    discussion_forum_activities_total_count = models.PositiveIntegerField(null=True)
    pass_grade = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    question_name = models.CharField(max_length=500, null=True)
    avg_before_lo_score = models.DecimalField(max_digits=38, decimal_places=2, null=True)
    avg_after_lo_score = models.DecimalField(max_digits=38, decimal_places=2, null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return "<EnterpriseExecEdLCModulePerformance User {user} of {enterprise} in module {module}>".format(
            user=self.ocm_lms_user_id,
            enterprise=self.enterprise_customer_uuid,
            module=self.module_number,
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()
