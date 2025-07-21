from rest_framework import serializers
from procurement.models import ProcurementOrder, ProcurementOrderLine
from procurement.serializers.procurement_order_line_serializers import ProcurementOrderLineSerializer
from core.models import Company
from core.serializers.company_serializers import CompanySerializer

class ProcurementOrderSerializer(serializers.ModelSerializer):
    lines = ProcurementOrderLineSerializer(many=True, required=False)
    vendor = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    total_price_without_tax = serializers.SerializerMethodField(read_only=True)
    total_price_with_tax = serializers.SerializerMethodField(read_only=True)
    all_received = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProcurementOrder
        fields = [
            'id',
            'vendor',
            'payment_term',
            'payment_method',
            'incoterms',
            'trade_discount',
            'due_in_days',
            'due_discount',
            'due_discount_days',
            'invoice_accepted',
            'description',
            'status',
            'currency',
            'delivery_address',
            'lines',
            'created_by',
            'created_at',
            'total_price_without_tax',
            'total_price_with_tax',
            'all_received',
        ]
        read_only_fields = ['created_by', 'created_at', 'total_price_without_tax', 'total_price_with_tax', 'all_received']
    
    def get_total_price_without_tax(self, obj):
        return obj.total_price_without_tax

    def get_total_price_with_tax(self, obj):
        return obj.total_price_with_tax

    def get_all_received(self, obj):
        return obj.all_received

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        action = self.context.get('action')
        if action == 'retrieve':
            ret['lines'] = ProcurementOrderLineSerializer(instance.lines.all(), many=True, context=self.context).data
            ret['vendor'] = CompanySerializer(instance.vendor, context=self.context).data if instance.vendor else None
        elif action == 'list':
            ret['vendor'] = getattr(instance.vendor, 'name', None)
            ret['lines_count'] = instance.lines.count()
        return ret

    def create(self, validated_data):
        payment_term = validated_data.get('payment_term')
        errors = {}
        
        if payment_term in ['NET_T', 'T_EOM', 'PARTIAL_ADVANCE']:
            if not validated_data.get('due_in_days'):
                errors['due_in_days'] = 'Bu vade tipi için vade günü gereklidir.'

        if payment_term == 'X_Y_NET_T':
            if not validated_data.get('due_discount'):
                errors['due_discount'] = 'İskontolu net vade için vade iskontosu gereklidir.'
                
            if not validated_data.get('due_discount_days'):
                errors['due_discount_days'] = 'İskontolu net vade için vade iskonto günü gereklidir.'
        if errors:
            raise serializers.ValidationError(errors)
        lines_data = validated_data.pop('lines', None)
        order = ProcurementOrder.objects.create(**validated_data)
        if lines_data:
            for line_data in lines_data:
                line_data['po'] = order
                ProcurementOrderLineSerializer().create(line_data)
        return order

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
        # Only allow partial update if PO is draft
        if instance.status != 'draft':
            raise serializers.ValidationError({'status': 'Sadece taslak (draft) durumundaki PO güncellenebilir.'})
        allowed_fields = [
            'payment_term', 'payment_method', 'incoterms', 'trade_discount',
            'due_in_days', 'due_discount', 'due_discount_days', 'invoice_accepted',
            'description', 'currency', 'delivery_address'
        ]
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        # Handle status change only via custom action context
        action = self.context.get('action')
        if action and action.startswith('set_status_'):
            new_status = action.replace('set_status_', '')
            instance.status = new_status
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
