from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from sales.models import SalesOrderLine
from core.serializers.material_serializers import MaterialSerializer

class SalesOrderLineSerializer(serializers.ModelSerializer):
    material_internal_code = serializers.CharField(source='material.internal_code', read_only=True)
    created_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrderLine
        fields = [
            'id',
            'so',
            'material',
            'material_internal_code',
            'quantity',
            'uom',
            'unit_price',
            'tax_rate',
            'created_by',
            'created_at',
            
        ]
        read_only_fields = [
            'material_internal_code',
            'created_by',
            'created_at'
        ]
        
    def get_created_by(self, obj):
        first_history = getattr(obj, 'history', None)
        if first_history:
            first_history = first_history.order_by('history_date').first()
            if first_history and hasattr(first_history, 'history_user') and first_history.history_user:
                return str(first_history.history_user)
        return None

    def get_created_at(self, obj):
        first_history = getattr(obj, 'history', None)
        if first_history:
            first_history = first_history.order_by('history_date').first()
            if first_history:
                return first_history.history_date
        return None
    
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


    def validate(self, attrs):
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
        so = validated_data.get('so')
        material = validated_data.get('material')
        if so:
            if so.status != 'draft':
                raise serializers.ValidationError({
                    'po': 'Sadece taslak (draft) durumundaki SO için satır eklenebilir.'
                })
        if so and material:
            exists = SalesOrderLine.objects.filter(po=so, material=material).exists()
            if exists:
                raise serializers.ValidationError({
                    'material': 'Bu malzeme bu SO da zaten mevcut!.'
                })
        return SalesOrderLine.objects.create(**validated_data)
    
    
    def update(self, instance, validated_data):
        parent_status = instance.so.status if hasattr(instance, 'so') and instance.so else None
        
        if parent_status:
            
            if parent_status == 'draft':

                allowed_fields = ['tax_rate', 'quantity', 'uom', 'unit_price']
                disallowed = []
                for field in validated_data:
                    if field not in allowed_fields:
                        disallowed.append(field)
                        
                if disallowed:
                    raise serializers.ValidationError({
                        'fields': f"Taslak (draft) SO'da sadece tax_rate, quantity, uom ve unit_price güncellenebilir."
                    })
            else:
                raise serializers.ValidationError({
                    'fields': f"SO durumu '{parent_status}' olduğunda bir şey güncellenemez."
                })
                
        for field in validated_data:
            setattr(instance, field, validated_data[field])
            
        instance.save()
        return instance