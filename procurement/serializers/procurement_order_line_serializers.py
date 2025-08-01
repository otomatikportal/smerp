from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from core.serializers.material_serializers import MaterialSerializer
from procurement.models import ProcurementOrderLine, ProcurementOrder


class ProcurementOrderLineSerializer(serializers.ModelSerializer):
    po = serializers.PrimaryKeyRelatedField(queryset=ProcurementOrder.objects.all(), required=False)
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.DecimalField(max_digits=21, decimal_places=2, coerce_to_string=False)
    quantity_received = serializers.DecimalField(max_digits=21, decimal_places=2, coerce_to_string=False, read_only=True)
    unit_price = serializers.DecimalField(max_digits=32, decimal_places=2, coerce_to_string=False, required=False, allow_null=True)
    tax_rate = serializers.DecimalField(max_digits=4, decimal_places=3, coerce_to_string=False, required=False, allow_null=True)

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
        read_only_fields = [
            'quantity_left',
            'total_with_tax',
            'total_without_tax',
            'created_by',
            'created_at',
            'quantity_received'
            ]

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
    
    def validate(self, attrs):
        # Use self.partial to determine if this is a partial update
        uom = attrs.get('uom')
        quantity = attrs.get('quantity')
        if getattr(self, 'partial', False):
            instance = getattr(self, 'instance', None)
            if instance:
                if uom is None:
                    uom = getattr(instance, 'uom', None)
                if quantity is None:
                    quantity = getattr(instance, 'quantity', None)
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise serializers.ValidationError({
                    'quantity': _('Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.')
                })
        return attrs
        
    
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
    
    def update(self, instance, validated_data):
        parent_status = instance.po.status if instance.po else None
        if parent_status:
            if parent_status == 'draft':
                allowed_fields = ['tax_rate', 'quantity', 'uom', 'unit_price']
                
                disallowed = []
                for field in validated_data:
                    if field not in allowed_fields:
                        disallowed.append(field)
                        
                if disallowed:
                    raise serializers.ValidationError({
                        'fields': f"Taslak (draft) PO'da sadece quantity_received, tax_rate, quantity, uom ve unit_price güncellenebilir."
                    })
            else:
                raise serializers.ValidationError({
                    'fields': f"PO durumu '{parent_status}' olduğunda bir şey güncellenemez."
                })
        for field in validated_data:
            setattr(instance, field, validated_data[field])
        instance.save()
        return instance