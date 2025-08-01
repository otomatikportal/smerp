from rest_framework.generics import ListAPIView
from inventory.models import InventoryLocation
from inventory.serializers import InventoryLocationDropdownSerializer
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter

class InventoryLocationDropdownPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 25

class InventoryLocationDropdownView(ListAPIView):
    queryset = InventoryLocation.objects.all()
    serializer_class = InventoryLocationDropdownSerializer
    permission_classes = [AllowAny]
    pagination_class = InventoryLocationDropdownPagination
    filter_backends = [SearchFilter]
    search_fields = ['name']