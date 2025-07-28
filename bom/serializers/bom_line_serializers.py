from rest_framework import serializers
from bom.models import BomLine
from django.utils.translation import gettext_lazy as _


class BomLineSerializer(serializers.ModelSerializer):
    
    created_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    uom = serializers.CharField()
    material_internal_code = serializers.SerializerMethodField()
    
    class Meta:
        model = BomLine
        fields = [
            'bom',
            'component',
            'quantity',
            'uom',
            'material_internal_code',
            'created_by',
            'created_at'
        ]
        read_only_fields = [
            'created_by',
            'created_at',
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
        if obj.component and hasattr(obj.component, 'internal_code'):
            return obj.component.internal_code
        return None
    
    def validate_uom(self, value):
        if not value:
            raise serializers.ValidationError(_("UOM alanı zorunludur ve boş bırakılamaz."))
        return value
    
    def validate(self, data):
        quantity = data.get('quantity')
        uom = data.get('uom')
        
        if quantity and uom:
            if uom in ['ADT', 'BOX', 'PLT'] and quantity != int(quantity):
                raise serializers.ValidationError({
                    'quantity': _("Adet, koli ve palet birimleri için miktar tam sayı olmalıdır.")
                })
        
        return data
        
    
