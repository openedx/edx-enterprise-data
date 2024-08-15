"""Custom paginator for the Advance Analytics API."""

import math
from dataclasses import dataclass
from typing import Any

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


@dataclass
class Page:
    """
    A class representing a single page of paginated data.

    Attributes:
        data (Any): The data contained in the current page.
        count (int): The total number of items across all pages.
        num_pages (int): The total number of pages.
        current_page (int): The current page number.
    """
    data: Any
    count: int
    num_pages: int
    current_page: int

    def has_next(self):
        """
        Check if there is a next page.

        Returns:
            bool: True if there is a next page, False otherwise.
        """
        return self.current_page < self.num_pages

    def has_previous(self):
        """
        Check if there is a previous page.

        Returns:
            bool: True if there is a previous page, False otherwise.
        """
        return self.current_page > 1

    def next_page_number(self):
        """
        Get the next page number.

        Returns:
            int: The next page number.
        """
        return self.current_page + 1

    def previous_page_number(self):
        """
        Get the previous page number.

        Returns:
            int: The previous page number.
        """
        return self.current_page - 1


class AdvanceAnalyticsPagination(PageNumberPagination):
    """
    Custom pagination class for advanced analytics.

    Attributes:
        page_size_query_param (str): The query parameter for the page size.
        page_size (int): The default page size.
        max_page_size (int): The maximum allowed page size.
    """
    page_size_query_param = "page_size"
    page_size = 50
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a given dataframe based on the request parameters.

        Args:
            queryset (pd.DataFrame): The dataframe to paginate.
            request (Request): The request object containing query parameters.
            view (View, optional): The view that is calling the paginator.

        Returns:
            Page: A Page object. `data` attribute of the object will contain the paginated data.
        """
        dataframe = queryset

        self.request = request  # pylint: disable=attribute-defined-outside-init
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        total_rows = dataframe.shape[0]
        num_pages = math.ceil(total_rows / page_size)

        page_number = int(request.query_params.get(self.page_query_param) or 1)
        if page_number <= 0 or page_number > num_pages:
            raise NotFound('Invalid page.')

        start_index = (page_number - 1) * page_size
        end_index = min(start_index + page_size, total_rows)
        data_frame_page = dataframe.iloc[start_index:end_index]

        # pylint: disable=attribute-defined-outside-init
        self.page = Page(data_frame_page, total_rows, num_pages, page_number)

        return self.page

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.count,
            'num_pages': self.page.num_pages,
            'current_page': self.page.current_page,
            'results': data
        })
