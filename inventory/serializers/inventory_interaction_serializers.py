from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.templatetags.rest_framework import TRAILING_PUNCTUATION
from core.fields import UOMField
from core.serializers.material_serializers import MaterialSerializer
from core.models import Material
from inventory.models import InventoryLocation
from procurement.models import ProcurementOrderLine
from decimal import Decimal


class IncomingItemsListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True)
    vendor = serializers.CharField(source="po.vendor.name", read_only=True)
    material = serializers.PrimaryKeyRelatedField(read_only=True)
    material_internal_code = serializers.CharField(source="material.internal_code", read_only=True)
    quantity = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)
    uom = serializers.CharField(read_only=True)
    quantity_received = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)
    quantity_left = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)

# For detail views
class IncomingItemsDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True)
    vendor = serializers.CharField(source="po.vendor.name", read_only=True)
    material = MaterialSerializer(read_only=True)  # Nested serializer
    material_internal_code = serializers.CharField(source="material.internal_code", read_only=True)
    quantity = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)
    uom = serializers.CharField(read_only=True)
    quantity_received = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)
    quantity_left = serializers.DecimalField(max_digits=21, decimal_places=2, read_only=True)
    
    

class SimpleInventoryTransactionSerializer(serializers.Serializer):
    location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all())
    quantity = serializers.DecimalField(max_digits=30, decimal_places=2, min_value=Decimal('0'))
    change_reason = serializers.CharField(max_length=100, required=False)
    source_id = serializers.PrimaryKeyRelatedField(queryset=ProcurementOrderLine.objects.all())
    
    def validate_source_id(self, value):
        if value.po.status not in ['ordered', 'billed', 'paid']:
            raise serializers.ValidationError(_("PO işlenmeye uygun statüde değil!"))
        return value
    
    def validate(self, data):
        
        source_id = data['source_id']
        data['material'] = source_id.material
        data['uom'] = source_id.uom
        return data
        
        
    
    
    
    