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
    
    class Meta:
        model = Bom
        fields = [
            'product',
            'uom',
            'labor_cost',
            'machining_cost',
            'lines',
            'material_internal_code',
            'created_by',
            'created_at'
        ]
        read_only_fields = [
            'created_at',
            'created_by',
            'material_internal_code'
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
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        bom = Bom.objects.create(**validated_data)
        
        for line_data in lines_data:
            line_data['bom'] = bom.pk
            line_serializer = BomLineSerializer(data=line_data)
            if line_serializer.is_valid(raise_exception=True):
                line_serializer.save()
        
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
        