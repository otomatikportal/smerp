from rest_framework import serializers
from inventory.models import InventoryLocation
from inventory.serializers.stock_record_serializers import StockRecordSerializer

class InventoryLocationSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InventoryLocation
        fields = [
            'id',
            'name',
            'facility',
            'area',
            'section',
            'shelf',
            'bin',
            'type',
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
            stock_records = instance.stockrecord_set.all()
            items_context = self.context.copy()
            items_context['action'] = 'list'
            ret['items'] = StockRecordSerializer(stock_records, many=True, context=items_context).data
        elif action == 'list':
            pass
        return ret

    def update(self, instance, validated_data):
        # Only allow updating name, facility, area, section, shelf, bin, type
        allowed_fields = ['name', 'facility', 'area', 'section', 'shelf', 'bin', 'type']
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
