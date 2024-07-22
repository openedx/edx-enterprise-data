"""
Views for enterprise offers
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from enterprise_data.api.v1 import serializers
from enterprise_data.models import EnterpriseOffer

from .base import EnterpriseViewSetMixin


class EnterpriseOfferViewSet(EnterpriseViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Viewset for enterprise offers.
    """
    serializer_class = serializers.EnterpriseOfferSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend,)
    ordering_fields = '__all__'

    lookup_field = 'offer_id'

    filterset_fields = (
        'offer_id',
        'status'
    )

    def get_object(self):
        """
        This ensures that UUIDs with dashes are properly handled when requesting info about offers.

        Related to the work in EnterpriseOfferSerializer with `to_internal_value` and `to_representation`
        """
        self.kwargs['offer_id'] = self.kwargs['offer_id'].replace('-', '')
        return super().get_object()

    def get_queryset(self):
        enterprise_customer_uuid = self.kwargs['enterprise_id']
        return EnterpriseOffer.objects.filter(
            enterprise_customer_uuid=enterprise_customer_uuid,
        )
