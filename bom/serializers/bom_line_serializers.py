from rest_framework import serializers
from bom.models import BomLine


class BomLineSerializer(serializers.ModelSerializer):
    
    created_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = BomLine
        fields = [
            'bom',
            'component',
            'quantity',
            'uom',
            'created_by',
            'created_at'
        ]
        read_only_fields = [
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
            