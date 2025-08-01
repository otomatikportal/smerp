from rest_framework.generics import ListAPIView
from inventory.models import InventoryLocation
from inventory.serializers.dropdown_serializers import InventoryLocationDropdownSerializer
from rest_framework.permissions import AllowAny

class InventoryLocationDropdownView(ListAPIView):
    queryset = InventoryLocation.objects.all()
    serializer_class = InventoryLocationDropdownSerializer
    permission_classes = [AllowAny]