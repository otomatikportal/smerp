from inventory.models import InventoryBalance
from rest_framework import serializers
from decimal import Decimal

class InventoryBalanceSerializer(serializers.ModelSerializer):
    material_internal_code = serializers.CharField(source='material.internal_code', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_description = serializers.CharField(source='material.description', read_only=True)
    display_quantity = serializers.SerializerMethodField()
    latest_entry = serializers.SerializerMethodField()
    latest_exit = serializers.SerializerMethodField()

    class Meta:
        model = InventoryBalance
        fields =[
            'id',
            'material_internal_code',
            'material_name',
            'display_quantity',
            'material_description',
            'latest_entry',
            'latest_exit'
        ]
        read_only_fields = fields

    def get_display_quantity(self, obj):
        value = obj.quantity
        uom = obj.uom
        uom_display = uom
        if hasattr(obj, 'get_uom_display'):
            uom_display = obj.get_uom_display()
        # For ADT, PLT, BOX show as integer, else as Turkish decimal
        if uom in ("ADT", "PLT", "BOX"):
            try:
                quantized = int(Decimal(value))
            except Exception:
                quantized = int(value)
            s = f"{quantized:,}".replace(",", ".")
        else:
            try:
                quantized = Decimal(value).quantize(Decimal('0.01'))
            except Exception:
                quantized = value
            s = f"{quantized:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        return f"{s} {uom_display}"
    
    
    def get_latest_entry(self, obj):
        from inventory.models.stock_movement import StockMovement
        qs = StockMovement.objects.filter(
            material=obj.material,
            uom=obj.uom,
            action=StockMovement.Action.IN
        ).order_by('-created_at')
        latest = qs.first()
        if latest:
            return latest.created_at
        return None

    def get_latest_exit(self, obj):
        from inventory.models.stock_movement import StockMovement
        qs = StockMovement.objects.filter(
            material=obj.material,
            uom=obj.uom,
            action=StockMovement.Action.OUT
        ).order_by('-created_at')
        latest = qs.first()
        if latest:
            return latest.created_at
        return None
        


