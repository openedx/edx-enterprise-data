"""
Enterprise Data Paginators.
"""

from collections import OrderedDict
from django.http import JsonResponse
from requests.models import PreparedRequest

from django.core.paginator import Paginator
from edx_rest_framework_extensions.paginators import DefaultPagination


class EnterpriseEnrollmentsPagination(DefaultPagination):
    """
    Pagination format used by Enterprise Enrollments API.
    """

    max_page_size = 1000


class ListPaginator:
    def __init__(self, request):
        self._url = request.url

    def paginate_list(self, data, page_size=50, page_number=1):
        paginator = Paginator(data, page_size)
        page = paginator.page(page_number)
        prepared_request = PreparedRequest()

        previous_url = None
        next_url = None
        if self._url:
            if page.has_previous():
                params = {'limit': page_size, 'page': page.previous_page_number()}
                prepared_request.prepare_url(self._url, params)
                previous_url = prepared_request.url
            if page.has_next():
                params = {'limit': page_size, 'page': page.next_page_number()}
                prepared_request.prepare_url(self._url, params)
                next_url = prepared_request.url

        response_dict = OrderedDict([
            ('count', len(data)),
            ('next', next_url),
            ('previous', previous_url),
            ('results', page.object_list)
        ])
        return JsonResponse(response_dict, status=200, safe=False)
