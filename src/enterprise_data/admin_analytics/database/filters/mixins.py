"""
Common query filters for all tables.
"""
from logging import getLogger
from typing import Optional, Tuple
from uuid import UUID

from enterprise_data.admin_analytics.database.filters.base import BaseFilter
from enterprise_data.admin_analytics.database.query_filters import BetweenQueryFilter, EqualQueryFilter, INQueryFilter
from enterprise_data.clients import EnterpriseApiClient
from enterprise_data.exceptions import EnterpriseApiClientException

LOGGER = getLogger(__name__)


class CommonFiltersMixin(BaseFilter):
    """
    Common filters.
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
    def date_range_filter(
        column: str,
        start_date_params_key: str,
        end_date_params_key: str
    ) -> BetweenQueryFilter:
        """
        Filter by a table column to be in the given date range.

        Arguments:
            column (str): The table column name to filter on.
            start_date_params_key (str): The start date key against which value will be passed in the query.
            end_date_params_key (str): The end date key against which value will be passed in the query.
        """
        return BetweenQueryFilter(
            column=column,
            range_placeholders=(start_date_params_key, end_date_params_key),
        )

    def enterprise_user_query_filter(  # pylint: disable=inconsistent-return-statements
        self,
        group_uuid: Optional[UUID],
        enterprise_customer_uuid: UUID
    ) -> Optional[Tuple[INQueryFilter, dict]]:
        """
        Get the query filter to filter enrollments for enterprise users in the given group.

        Arguments:
            group_uuid (UUID): The UUID of the group.
            enterprise_customer_uuid (UUID): The UUID of the enterprise customer.

        Returns:
            (INQueryFilter | None): The query filter to filter enrollments for enterprise users in the given group.
        """
        if not group_uuid:
            return None

        try:
            learners_in_group = EnterpriseApiClient.get_enterprise_user_ids_in_group(group_uuid)
        except EnterpriseApiClientException:
            LOGGER.exception(
                "Failed to get learners in group [%s] for enterprise [%s]",
                group_uuid,
                enterprise_customer_uuid,
            )
        else:
            params = {f'eu_{i}': i for i in learners_in_group}
            enterprise_user_id_in_filter = INQueryFilter(
                column='enterprise_user_id',
                values_placeholders=list(params.keys()),
            )
            return enterprise_user_id_in_filter, params
