from decimal import Decimal
from rest_framework import serializers
from procurement.models import ProcurementOrder, ProcurementOrderLine
from procurement.serializers.procurement_order_line_serializers import ProcurementOrderLineSerializer
from core.models import Company
from core.serializers.company_serializers import CompanySerializer
from django.utils.translation import gettext_lazy as _

class ProcurementOrderSerializer(serializers.ModelSerializer):
    lines = ProcurementOrderLineSerializer(many=True, required=False)
    vendor = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProcurementOrder
        fields = [
            'id',
            'po_number',
            'payment_term',
            'payment_method',
            'incoterms',
            'trade_discount',
            'due_in_days',
            'due_discount',
            'due_discount_days',
            'invoice_accepted',
            'invoice_date',
            'last_payment_date',
            'description',
            'status',
            'currency',
            'delivery_address',
            'created_by',
            'created_at',
            'total_price_without_tax',
            'total_price_with_tax',
            'all_received',
            'lines',
            'vendor',
        ]
        read_only_fields = [
            'created_by', 
            'created_at', 
            'total_price_without_tax', 
            'total_price_with_tax', 
            'all_received', 
            'last_payment_date', 
            'invoice_accepted',
            'po_number',
        ]
        
    def get_lines(self, obj):
        qs = obj.lines.all()
        return ProcurementOrderLineSerializer(qs, many=True, context=self.context).data

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
        # Remove status from validated_data (orders always start as 'draft')
        validated_data.pop('status', None)
        
        # Reset fields that shouldn't be set for certain payment terms
        payment_term = validated_data.get('payment_term')
        if payment_term not in ['NET_T', 'PARTIAL_ADVANCE']:
            validated_data['due_discount'] = Decimal('0.000')
            validated_data['due_discount_days'] = None

        lines_data = validated_data.pop('lines', None)
        order = ProcurementOrder.objects.create(**validated_data)

        if lines_data:
            for line_data in lines_data:
                line_data['po'] = order
                ProcurementOrderLineSerializer().create(line_data)
        return order

    def validate_payment_term(self, value):
        """Validate payment term field"""
        return value
    
    def validate_due_discount(self, value):
        """Validate due_discount based on payment_term"""
        # This will be cross-validated in validate() method
        return value
    
    def validate_due_discount_days(self, value):
        """Validate due_discount_days based on payment_term"""
        # This will be cross-validated in validate() method
        return value
    
    def validate(self, attrs):
        """Cross-field validation for payment terms"""
        payment_term = attrs.get('payment_term')
        due_in_days = attrs.get('due_in_days')
        due_discount = attrs.get('due_discount')
        due_discount_days = attrs.get('due_discount_days')
        
        errors = {}
        
        # Validate payment term requirements
        if payment_term in ['NET_T', 'PARTIAL_ADVANCE']:
            if not due_in_days:
                errors['due_in_days'] = _('Bu vade tipi için vade günü gereklidir.')
        else:
            # If payment_term is not in the allowed list, do not allow due_discount or due_discount_days
            if due_discount is not None and due_discount != Decimal('0.000'):
                errors['due_discount'] = _('Bu vade tipi için vade iskontosu girilemez.')
            if due_discount_days is not None:
                errors['due_discount_days'] = _('Bu vade tipi için vade iskonto günü girilemez.')
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
    
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

    def update(self, instance, validated_data):
        # Remove status from validated_data if present (status changes should use dedicated endpoint)
        validated_data.pop('status', None)
        
        # Handle special cases for non-draft statuses
        if instance.status in ['ordered', 'approved']:
            # Only allow invoice_date updates for ordered/approved orders
            allowed_fields = ['invoice_date']
            non_allowed_updates = [field for field in validated_data.keys() if field not in allowed_fields]
            if non_allowed_updates:
                status_display = dict(instance.STATUS).get(instance.status, instance.status)
                raise serializers.ValidationError({
                    'fields': _('%(status)s durumundaki siparişlerde sadece fatura tarihi güncellenebilir. Diğer işlemler için durum değiştirme endpoint\'lerini kullanın.') % {'status': status_display}
                })
            
            # Simple update for allowed fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        
        elif instance.status != 'draft':
            raise serializers.ValidationError({
                'status': _('Sadece taslak siparişler güncellenebilir. Diğer işlemler için durum değiştirme endpoint\'lerini kullanın.')
            })
        
        # Handle payment term validation for draft orders (keep this business rule)
        payment_term = validated_data.get('payment_term', instance.payment_term)
        errors = {}
        
        if payment_term not in ['NET_T', 'PARTIAL_ADVANCE']:
            if validated_data.get('due_discount') is not None:
                errors['due_discount'] = _('Bu vade tipi için vade iskontosu girilemez.')
            if validated_data.get('due_discount_days') is not None:
                errors['due_discount_days'] = _('Bu vade tipi için vade iskonto günü girilemez.')
            # Reset these fields if payment term doesn't support them
            if 'due_discount' not in validated_data:
                validated_data['due_discount'] = Decimal('0.000')
            if 'due_discount_days' not in validated_data:
                validated_data['due_discount_days'] = None
        
        if errors:
            raise serializers.ValidationError(errors)
        
        # Simple update for draft orders
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
