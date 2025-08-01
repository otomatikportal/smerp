
from rest_framework import pagination, status, permissions, filters, generics
from inventory.models import InventoryBalance
from inventory.serializers.inventory_get_serializers import InventoryBalanceSerializer
from rest_framework.response import Response

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": "Inventory balances retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class InventoryBalanceListAPIView(generics.ListAPIView):
    queryset = InventoryBalance.objects.exclude(quantity=0)
    serializer_class = InventoryBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['material__internal_code', 'material__name', 'material__description']
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        paginated = response.data
        if isinstance(paginated, dict):
            return Response(paginated, status=status.HTTP_200_OK)

class InventoryBalanceDetailAPIView(generics.RetrieveAPIView):
    queryset = InventoryBalance.objects.exclude(quantity=0)
    serializer_class = InventoryBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        data = {
            "message": "Inventory balance record retrieved succesfully",
            "status": "success",
            "result": response.data
        }
        return Response(data, status=status.HTTP_200_OK)
