"""
Query filters for enrollments table.
"""
from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.query_filters import BetweenQueryFilter, EqualQueryFilter, INQueryFilter


class FactEnrollmentAdminDashFilters(BaseFilter):
    """
    Query filters for enrollments table.
    """
    @staticmethod
    def enterprise_customer_uuid_filter(enterprise_customer_uuid_params_key: str) -> EqualQueryFilter:
        """
        Filter by enterprise customer uuid.

        Arguments:
            enterprise_customer_uuid_params_key: The key against which value will be passed in the query.
        """
        return EqualQueryFilter(
            column='enterprise_customer_uuid',
            value_placeholder=enterprise_customer_uuid_params_key,
        )

    @staticmethod
    def enterprise_enrollment_date_range_filter(
            start_date_params_key: str, end_date_params_key: str
    ) -> BetweenQueryFilter:
        """
        Filter by enrollment date to be in the given range.

        Arguments:
            start_date_params_key (str): The start date key against which value will be passed in the query.
            end_date_params_key (str): The end date key against which value will be passed in the query.
        """
        return BetweenQueryFilter(
            column='enterprise_enrollment_date',
            range_placeholders=(start_date_params_key, end_date_params_key),
        )

    @staticmethod
    def enterprise_user_id_in_filter(
            enterprise_user_id_param_keys: list,
    ) -> INQueryFilter:
        """
        Filter by enterprise user id.
        """
        return INQueryFilter(
            column='enterprise_user_id',
            values_placeholders=enterprise_user_id_param_keys
        )
