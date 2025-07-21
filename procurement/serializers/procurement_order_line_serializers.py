from rest_framework import serializers
from core.serializers.material_serializers import MaterialSerializer
from procurement.models import ProcurementOrderLine

class ProcurementOrderLineSerializer(serializers.ModelSerializer):
    quantity_left = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    total_with_tax = serializers.SerializerMethodField(label="Satır Toplamı (Vergi Dahil)")
    total_without_tax = serializers.SerializerMethodField(label="Satır Toplamı (Vergi Hariç)")

    class Meta:
        model = ProcurementOrderLine
        fields = [
            'id',
            'po',
            'material',
            'uom',
            'quantity',
            'quantity_received',
            'unit_price',
            'tax_rate',
            'quantity_left',
            'total_with_tax',
            'total_without_tax',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['quantity_left', 'total_with_tax', 'total_without_tax', 'created_by', 'created_at']
        
    def get_total_with_tax(self, obj):
        return obj.total_with_tax

    def get_total_without_tax(self, obj):
        return obj.total_without_tax

    def get_quantity_left(self, obj):
        return obj.quantity_left

    def get_created_by(self, obj):
        first_history = obj.history.order_by('history_date').first()
        if first_history and hasattr(first_history, 'history_user') and first_history.history_user:
            return str(first_history.history_user)
        return None

    def get_created_at(self, obj):
        first_history = obj.history.order_by('history_date').first()
        if first_history:
            return first_history.history_date
        return None

    def partial_update(self, instance, validated_data):
        allowed_fields = ['uom', 'quantity', 'quantity_received', 'unit_price', 'tax_rate']
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
    
    def create(self, validated_data):
        po = validated_data.get('po')
        material = validated_data.get('material')
        if po:
            if po.status != 'draft':
                raise serializers.ValidationError({
                    'po': 'Sadece taslak (draft) durumundaki PO için satır eklenebilir.'
                })
        if po and material:
            exists = ProcurementOrderLine.objects.filter(po=po, material=material).exists()
            if exists:
                raise serializers.ValidationError({
                    'material': 'Bu malzeme bu PO da zaten mevcut!.'
                })
        return ProcurementOrderLine.objects.create(**validated_data)

    def delete(self, instance):
        instance.delete()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        action = self.context.get('action')
        material = instance.material
        if action == 'retrieve':
            ret['material'] = MaterialSerializer(material, context=self.context).data
        elif action == 'list':
            ret['material_internal_code'] = getattr(material, 'internal_code', None)
            ret['material'] = getattr(material, 'internal_code', None)
        return ret
