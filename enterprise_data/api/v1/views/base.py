"""
Base views for enterprise data api v1.
"""
from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination

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
