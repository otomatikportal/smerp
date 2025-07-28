from rest_framework import serializers
from bom.models import Bom, BomLine
from bom.serializers.bom_line_serializers import BomLineSerializer
from django.utils.translation import gettext_lazy as _


class BomSerializer(serializers.ModelSerializer):
    
    created_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    uom = serializers.CharField()
    lines = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    material_internal_code = serializers.SerializerMethodField()
    latest_cost = serializers.SerializerMethodField(read_only = True)
    
    class Meta:
        model = Bom
        fields = [
            'id',
            'product',
            'uom',
            'labor_cost',
            'machining_cost',
            'lines',
            'material_internal_code',
            'latest_cost',
            'created_by',
            'created_at'
        ]
        read_only_fields = [
            'created_at',
            'created_by',
            'material_internal_code',
            'latest_cost',
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
    
    def get_material_internal_code(self, obj):
        if obj.product and hasattr(obj.product, 'internal_code'):
            return obj.product.internal_code
        return None
    
    def get_latest_cost(self, obj):
        return obj.latest_cost
    
    
    # Intentional bulk create modification to 
    # not trigger variable cost creation multiple timesé
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        bom = Bom.objects.create(**validated_data)
        
        bom_lines = []
        for line_data in lines_data:
            line_data['bom'] = bom.pk
            line_serializer = BomLineSerializer(data=line_data)
            if line_serializer.is_valid(raise_exception=True):
                
                # Create object but don't save yet
                bom_line = BomLine(
                    bom=bom,
                    component_id=line_data['component'],
                    quantity=line_data['quantity'],
                    uom=line_data['uom']
                )
                bom_lines.append(bom_line)
                
        if bom_lines:
            BomLine.objects.bulk_create(bom_lines)
            from bom.signals import create_variable_cost_for_bom_instance
            create_variable_cost_for_bom_instance(bom)
        
        return bom
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        action = self.context.get('action')
        
        if action == 'list':
            representation['count_of_lines'] = instance.lines.count()
        
        elif action == 'retrieve':
            lines = instance.lines.all()
            representation['lines'] = BomLineSerializer(lines, many=True, context={'action': 'list'}).data
        
        return representation
        