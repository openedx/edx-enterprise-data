"""
Enterprise Data Paginators.
"""


from edx_rest_framework_extensions.paginators import DefaultPagination


class EnterpriseEnrollmentsPagination(DefaultPagination):
    """
    Pagination format used by Enterprise Enrollments API.
    """

    max_page_size = 1000
