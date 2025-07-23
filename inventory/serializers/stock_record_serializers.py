from rest_framework import serializers
from inventory.models import StockRecord
from core.serializers.material_serializers import MaterialSerializer

class StockRecordSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StockRecord
        fields = [
            'id',
            'material',
            'uom',
            'quantity',
            'location',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']

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
        if action == 'retrieve':
            ret['material'] = MaterialSerializer(instance.material, context=self.context).data
        elif action == 'list':
            # Add material_internal_code from related material
            ret['material_internal_code'] = getattr(instance.material, 'internal_code', None)
        return ret
    
    def validate(self, attrs):
        uom = attrs.get('uom')
        quantity = attrs.get('quantity')
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise serializers.ValidationError({
                    'quantity': 'Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.'
                })
        return attrs

    def update(self, instance, validated_data):
        allowed_fields = ['material', 'uom', 'quantity', 'location']
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
