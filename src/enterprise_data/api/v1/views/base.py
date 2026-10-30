"""
Base views for enterprise data api v1.
"""
import math

from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from enterprise_data.constants import ANALYTICS_API_VERSION_1


class EnterpriseViewSetMixin(PermissionRequiredMixin):
    """
    Base class for all Enterprise view sets.
    """
    authentication_classes = (JwtAuthentication,)
    pagination_class = DefaultPagination
    permission_required = 'can_access_enterprise'
    API_VERSION = ANALYTICS_API_VERSION_1

    def paginate_queryset(self, queryset):
        """
        Allows no_page query param to skip pagination
        """
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)


class AnalyticsPaginationMixin:
    """
    Mixin that provides utility methods to allow pagination on views.
    """
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def get_next_link(self, request, page_number, page_count):
        """
        Get the link to the next page.

        Arguments:
            request (Request): The request object.
            page_number (int): The current page number.
            page_count (int): The total number of pages.

        Returns:
            str: The link to the next page.
        """
        if page_number >= page_count:
            return None
        return replace_query_param(
            url=request.build_absolute_uri(),
            key=self.page_query_param,
            val=page_number + 1,
        )

    def get_previous_link(self, request, page_number):
        """
        Get the link to the previous page.

        Arguments:
            request (Request): The request object.
            page_number (int): The current page number.

        Returns:
            str: The link to the previous page.
        """
        if page_number <= 1:
            return None
        url = request.build_absolute_uri()
        next_page = page_number - 1
        if next_page == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, next_page)

    def get_paginated_response(self, request, records, page, page_size, total_count):
        """
        Get pagination data.

        Arguments:
            request (Request): The request object.
            records (list): The records to return.
            page (int): The current page number.
            page_size (int): The number of records per page.
            total_count (int): The total number of records

        Returns:
            (Response): The pagination data.
        """
        page_count = math.ceil(total_count / page_size)
        if page_count > 0 and (page <= 0 or page > page_count):
            raise NotFound('Invalid page.')

        return Response({
            'next': self.get_next_link(request, page, page_count),
            'previous': self.get_previous_link(request, page),
            'count': total_count,
            'num_pages': page_count,
            'current_page': page,
            'results': records,
        })
