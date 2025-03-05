"""
Serializers for enterprise api v1.
"""
from uuid import UUID

from rest_framework import serializers

from enterprise_data.admin_analytics.constants import ResponseType
from enterprise_data.cache.decorators import cache_it
from enterprise_data.models import (
    EnterpriseAdminLearnerProgress,
    EnterpriseAdminSummarizeInsights,
    EnterpriseExecEdLCModulePerformance,
    EnterpriseGroupMembership,
    EnterpriseLearner,
    EnterpriseLearnerEnrollment,
    EnterpriseOffer,
    EnterpriseSubsidyBudget,
)
from enterprise_data.utils import calculate_percentage_difference


class EnterpriseLearnerEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearnerEnrollment model.
    """
    course_api_url = serializers.SerializerMethodField()
    enterprise_user_id = serializers.SerializerMethodField()
    total_learning_time_hours = serializers.SerializerMethodField()
    enterprise_flex_group_name = serializers.SerializerMethodField()
    enterprise_flex_group_uuid = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseLearnerEnrollment
        # Do not change the order of fields below. Ordering is important becuase `progress_v3`
        # csv generated in `enterprise_reporting` should be same as csv generated on `admin-portal`
        # Order and field names below should match with `EnrollmentsCSVRenderer.header`
        fields = (
            'enrollment_id', 'enterprise_enrollment_id', 'is_consent_granted', 'paid_by',
            'user_current_enrollment_mode', 'enrollment_date', 'unenrollment_date',
            'unenrollment_end_within_date', 'is_refunded', 'seat_delivery_method',
            'offer_id', 'offer_name', 'offer_type', 'coupon_code', 'coupon_name', 'contract_id',
            'course_list_price', 'amount_learner_paid', 'course_key', 'courserun_key',
            'course_title', 'course_pacing_type', 'course_start_date', 'course_end_date',
            'course_duration_weeks', 'course_max_effort', 'course_min_effort',
            'course_primary_program', 'primary_program_type', 'course_primary_subject', 'has_passed',
            'last_activity_date', 'progress_status', 'passed_date', 'current_grade',
            'letter_grade', 'enterprise_user_id', 'user_email', 'user_account_creation_date',
            'user_country_code', 'user_username', 'user_first_name', 'user_last_name', 'enterprise_name',
            'enterprise_customer_uuid', 'enterprise_sso_uid', 'created', 'course_api_url',
            'total_learning_time_hours', 'is_subsidy', 'course_product_line', 'budget_id',
            'enterprise_flex_group_name', 'enterprise_flex_group_uuid',
        )

    def get_course_api_url(self, obj):
        """Constructs course api url"""
        return '/enterprise/v1/enterprise-catalogs/{enterprise_customer_uuid}/courses/{courserun_key}'.format(
            enterprise_customer_uuid=obj.enterprise_customer_uuid, courserun_key=obj.courserun_key
        )

    def get_enterprise_user_id(self, obj):
        """Returns enterprise user id of a learner's enrollment"""
        return obj.enterprise_user_id

    def get_total_learning_time_hours(self, obj):
        """Returns the learners total learning time in hours"""
        return round((obj.total_learning_time_seconds or 0.0)/3600.0, 2)

    @cache_it()
    def _get_flex_groups(self, obj):
        """
        Returns list of tuples containing group (name, uuid) pairs for the learner.
        This is cached to prevent duplicate database queries.
        """
        enterprise_user_id = obj.enterprise_user_id

        if not enterprise_user_id:
            return []

        # Get all group memberships for this user in a single query
        # Order by name for consistent ordering
        return list(
            EnterpriseGroupMembership.objects.filter(
                enterprise_customer_user_id=enterprise_user_id,
                membership_is_removed=False,
                group_is_removed=False,
                group_type="flex",
            )
            .order_by("enterprise_group_name")
            .values_list("enterprise_group_name", "enterprise_group_uuid")
            .distinct()
        )

    def get_enterprise_flex_group_name(self, obj):
        """Returns a comma-separated list of enterprise group names that the learner is associated with"""
        groups = self._get_flex_groups(obj)

        if not groups:
            return obj.enterprise_group_name

        # Return comma-separated list of group names (first element of each tuple)
        return ', '.join(group[0] for group in groups)

    def get_enterprise_flex_group_uuid(self, obj):
        """Returns a comma-separated list of enterprise group UUIDs that the learner is associated with"""
        groups = self._get_flex_groups(obj)

        if not groups:
            return obj.enterprise_group_uuid

        # Return comma-separated list of group UUIDs (second element of each tuple)
        return ', '.join(str(group[1]) for group in groups)


class EnterpriseSubsidyBudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseSubsidyBudget model.
    """

    class Meta:
        model = EnterpriseSubsidyBudget
        exclude = ('id',)


class EnterpriseOfferSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseOfferSerializer model.
    """
    budgets = serializers.SerializerMethodField()

    def get_budgets(self, instance):
        """Gets related budgets"""

        try:
            # if offer_id is a uuid
            offer_uuid = UUID(instance.offer_id, version=4)
            budget_queryset = EnterpriseSubsidyBudget.objects.filter(subsidy_uuid=offer_uuid)
            serializer = EnterpriseSubsidyBudgetSerializer(instance=budget_queryset, many=True, read_only=True)
            return serializer.data
        except ValueError:
            pass

        return []

    class Meta:
        model = EnterpriseOffer
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Convert the incoming data offer_id field to a format that can be stored in the db.

        For a given offer_id string from the requester, determine the best representation to use for db storage.

        Raises serializers.ValidationError:
            If the given string is not exclusively numeric characters, but also does not parse as a UUID (either because
            it has the wrong length, incorrect dashes, or some other reason).
        """
        ret = super().to_internal_value(data)
        if ret['offer_id'] is None or ret['offer_id'] == '':
            raise serializers.ValidationError("requested offer_id is None.")

        if isinstance(ret['offer_id'], str) and len(ret['offer_id']) == 36:
            offer_id = ret['offer_id'].replace('-', '')
            # There should only be 4 dashes in the UUID, making the length 32 after removal
            if len(offer_id) == 32:
                ret['offer_id'] = offer_id
                return ret

            else:
                raise serializers.ValidationError("requested offer_id neither a valid integer nor UUID.")

        if len(ret['offer_id']) < 10:  # All ecommerce offer_ids are at < 1 million.
            try:
                int(ret['offer_id'])
                return ret
            except ValueError as e:
                raise serializers.ValidationError("Requested offer_id not a valid integer.") from e

        raise serializers.ValidationError("requested offer_id neither a valid integer nor UUID.")

    def to_representation(self, instance):
        """
        Add `-` dashes to the outgoing data offer_id field.
        """
        ret = super().to_representation(instance)

        # A 32 character offer_id is our heuristic for whether the stored value represents a UUID or integer.  If the
        # heuristic passes, make the serialized output look like a UUID.
        if len(ret['offer_id']) == 32:
            ret['offer_id'] = '-'.join([
                    ret['offer_id'][:8],
                    ret['offer_id'][8:12],
                    ret['offer_id'][12:16],
                    ret['offer_id'][16:20],
                    ret['offer_id'][20:]
                ]
            )

        return ret


class EnterpriseLearnerSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseLearner model.
    """

    class Meta:
        model = EnterpriseLearner
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if hasattr(instance, 'enrollment_count'):
            representation['enrollment_count'] = instance.enrollment_count
        if hasattr(instance, 'course_completion_count'):
            representation['course_completion_count'] = instance.course_completion_count

        return representation


class LearnerCompletedCoursesSerializer(serializers.Serializer):    # pylint: disable=abstract-method
    """
    Serializer for learner's completed courses.
    """
    class Meta:
        ref_name = 'v1.LearnerCompletedCoursesSerializer'

    user_email = serializers.EmailField()
    completed_courses = serializers.IntegerField()


class EnterpriseAdminLearnerProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseAdminLearnerProgress model.
    """

    class Meta:
        model = EnterpriseAdminLearnerProgress
        fields = '__all__'


class EnterpriseAdminSummarizeInsightsSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseAdminSummarizeInsights model.
    """

    class Meta:
        model = EnterpriseAdminSummarizeInsights
        fields = '__all__'


class AdminAnalyticsAggregatesQueryParamsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for validating admin analytics query params.
    """
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    granularity = serializers.CharField(required=False)
    calculation = serializers.CharField(required=False)
    response_type = serializers.CharField(required=False)
    page = serializers.IntegerField(required=False)
    chart_type = serializers.CharField(required=False)

    def validate(self, attrs):
        """
        Validate the query params.

        Raises:
            serializers.ValidationError: If start_date is greater than end_date.
        """
        if 'start_date' in attrs and 'end_date' in attrs:
            if attrs['start_date'] > attrs['end_date']:
                raise serializers.ValidationError("start_date should be less than or equal to end_date.")
        return attrs


class EnterpriseExecEdLCModulePerformanceSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseExecEdLCModulePerformance model.
    """
    extensions_requested = serializers.SerializerMethodField()
    avg_lo_percentage_difference = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseExecEdLCModulePerformance
        fields = '__all__'

    def get_extensions_requested(self, obj):
        """Return extensions_requested if not None, otherwise return 0"""
        return obj.extensions_requested if obj.extensions_requested is not None else 0

    def get_avg_lo_percentage_difference(self, obj):
        """
        Return percentage difference between `avg_before_lo_score` and `avg_after_lo_score` if not None,
        otherwise return None
        """
        if obj.avg_before_lo_score is None or obj.avg_after_lo_score is None:
            return None
        return round(
            calculate_percentage_difference(obj.avg_before_lo_score, obj.avg_after_lo_score),
            2
        )


class EnterpriseBudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseSubsidyBudget model.
    """

    class Meta:
        model = EnterpriseSubsidyBudget
        fields = (
            'subsidy_access_policy_uuid',
            'subsidy_access_policy_display_name',
        )


class EnterpriseGroupMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for EnterpriseGroupMembership model.
    """

    class Meta:
        model = EnterpriseGroupMembership
        fields = (
            'enterprise_group_uuid',
            'enterprise_group_name',
        )


class AdvanceAnalyticsQueryParamSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for validating query params"""
    RESPONSE_TYPES = [
        ResponseType.JSON.value,
        ResponseType.CSV.value
    ]
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    response_type = serializers.CharField(required=False)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=2)

    def validate(self, attrs):
        """
        Validate the query params.

        Raises:
            serializers.ValidationError: If start_date is greater than end_date.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date should be less than or equal to end_date.")

        return attrs

    def validate_response_type(self, value):
        """
        Validate the response_type value.

        Raises:
            serializers.ValidationError: If response_type is not one of the valid choices in `RESPONSE_TYPES`.
        """
        if value not in self.RESPONSE_TYPES:
            raise serializers.ValidationError(f"response_type must be one of {self.RESPONSE_TYPES}")
        return value
