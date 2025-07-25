from rest_framework import serializers
from sales.models import VariableCost
from core.serializers.material_serializers import MaterialSerializer

class VariableCostSerializer(serializers.ModelSerializer):
    procurement_order = serializers.SerializerMethodField(read_only = True)
    cost = serializers.DecimalField(max_digits=21, decimal_places=2, coerce_to_string=False)
    material_internal_code = serializers.CharField(source='material.internal_code', read_only=True)
    created_at = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField(read_only = True)
    
    class Meta:
        model = VariableCost

        fields = [
            'id',
            'material_internal_code',
            'cost',
            'uom',
            'source_type',
            'procurement_order',
            'user',
            'created_by',
            'created_at',
            'material',
        ]

        read_only_fields = [
            'created_by',
            'created_at',
            'source_type',
            'procurement_order',
            'material_internal_code'
        ]

    def get_procurement_order(self, obj):
        if obj.procurement_order:
            return str(obj.procurement_order)
        return None

    def get_user(self, obj):
        if obj.user:
            return str(obj.user)
        return None

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
        
        # Check if this is a retrieve action
        view = self.context.get('view')
        if view and hasattr(view, 'action') and view.action == 'retrieve':
            # Nest material serializer for detail view
            ret['material'] = MaterialSerializer(instance.material, context=self.context).data
        return ret
           



