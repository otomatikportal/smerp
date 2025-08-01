from rest_framework import serializers
from inventory.models import InventoryLocation

class InventoryLocationDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLocation
        fields = ['id', 'name']