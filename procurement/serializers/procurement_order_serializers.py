from decimal import Decimal
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
            'invoice_date',
            'last_payment_date',
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
        read_only_fields = [
            'created_by', 'created_at', 'total_price_without_tax', 'total_price_with_tax', 'all_received', 'last_payment_date', 'invoice_accepted'
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
        validated_data.pop('status', None)
        payment_term = validated_data.get('payment_term')
        errors = {}

        if payment_term in ['NET_T', 'T_EOM', 'PARTIAL_ADVANCE', 'X_Y_NET_T']:
            if not validated_data.get('due_in_days'):
                errors['due_in_days'] = 'Bu vade tipi için vade günü gereklidir.'

        else:
            # If payment_term is not in the allowed list, do not allow due_discount or due_discount_days
            if validated_data.get('due_discount') is not None:
                errors['due_discount'] = 'Bu vade tipi için vade iskontosu girilemez.'
            if validated_data.get('due_discount_days') is not None:
                errors['due_discount_days'] = 'Bu vade tipi için vade iskonto günü girilemez.'

        if payment_term == 'X_Y_NET_T':
            if not validated_data.get('due_discount'):
                errors['due_discount'] = 'İskontolu net vade için vade iskontosu gereklidir.'
            if not validated_data.get('due_discount_days'):
                errors['due_discount_days'] = 'İskontolu net vade için vade iskonto günü gereklidir.'
        if errors:
            raise serializers.ValidationError(errors)

        lines_data = validated_data.pop('lines', None)
        order = ProcurementOrder.objects.create(**validated_data)
        print(lines_data)

        if lines_data:
            for line_data in lines_data:
                print('debug execute')
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

    def update(self, instance, validated_data):
       
        action = self.context.get('action')
        validated_data.pop('status', None)
        
        STATUS = [
            'draft', 'submitted', 'approved', 'rejected', 'ordered', 'billed', 'paid', 'cancelled'
        ]

        if action and action.startswith('set_status_'):
            new_status = action.replace('set_status_', '')
            
            errors = {}
            if new_status == 'draft':
                
                if instance.status not in ['submitted', 'rejected', 'cancelled']:
                    errors['status'] = 'Geçerli durumda değil'
            
            elif new_status == 'submitted':
                if instance.lines.count() <= 0:
                    errors['lines'] = 'Satın almanın içinde malzeme yok'
                # Check for missing unit_price in any line
                missing_price_lines = [line for line in instance.lines.all() if line.unit_price is None]
                if missing_price_lines:
                    errors['lines'] = 'Satırların bir veya daha fazlasında birim fiyat eksik.'

                if instance.status != 'draft':
                    errors['status'] = 'Geçerli durumda değil'
                    
                required_fields = ['payment_term', 'vendor', 'payment_method', 'incoterms', 'description', 'currency', 'delivery_address']
                for field in required_fields:
                    if not getattr(instance, field, None):
                        errors[field] = f"'{field}' alanı gereklidir."

                if instance.payment_term in ['NET_T', 'T_EOM', 'PARTIAL_ADVANCE', 'X_Y_NET_T']:
                    if not getattr(instance, 'due_in_days', None):
                        errors['due_in_days'] = 'Bu vade tipi için vade günü gereklidir.'

                if instance.payment_term == 'X_Y_NET_T':
                    if not getattr(instance, 'due_discount', None):
                        errors['due_discount'] = 'İskontolu net vade için vade iskontosu gereklidir.'
                    if not getattr(instance, 'due_discount_days', None):
                        errors['due_discount_days'] = 'İskontolu net vade için vade iskonto günü gereklidir.'
                
                        
            elif new_status in ['approved', 'rejected']:
                
                if instance.status not in ['submitted', 'approved', 'rejected']:
                    errors['status'] = 'Geçerli durumda değil'
                    
            elif new_status == 'cancelled':
                
                if instance.status not in ['submitted', 'approved', 'ordered', 'draft']:         
                    errors['status'] = 'Bu durumda iptal edilemez, yöneticiye danışın'
                    
            elif new_status == 'ordered':
                
                if instance.status != 'approved':
                    errors['status'] = 'Onaylanmadan sipariş verilemez'
            
            elif new_status == 'billed':
                if instance.status != 'ordered':
                    errors['status'] = 'Sipariş verilmeden fatura girilemez'
                    
                invoice_date = validated_data.get('invoice_date')
                if not invoice_date and not getattr(instance, 'invoice_date', None):
                    errors['invoice_date'] = "Faturalandı durumunda 'invoice_date' alanı gereklidir."
                
                if invoice_date:
                    instance.invoice_date = invoice_date
                    
            elif new_status == 'paid':
                
                if instance.status != 'billed':
                    errors['status'] = 'Fatura tarihi girilmeden ödendi bilgisi verilemez'
                
            if errors:
                raise serializers.ValidationError(errors)
            instance.status = new_status
            instance.save()
            return instance


        
        allowed_fields = [
            'payment_term', 'payment_method', 'incoterms', 'trade_discount',
            'due_in_days', 'due_discount', 'due_discount_days',
            'description', 'currency', 'delivery_address'
        ]
        status = instance.status
        if status == 'draft':
            # Only allow allowed_fields to be changed
            payment_term = validated_data.get('payment_term', instance.payment_term)
            errors = {}
            if payment_term not in ['NET_T', 'T_EOM', 'PARTIAL_ADVANCE', 'X_Y_NET_T']:
                if validated_data.get('due_discount') is not None:
                    errors['due_discount'] = 'Bu vade tipi için vade iskontosu girilemez.'
                if validated_data.get('due_discount_days') is not None:
                    errors['due_discount_days'] = 'Bu vade tipi için vade iskonto günü girilemez.'
                if 'due_discount' not in validated_data:
                    instance.due_discount = Decimal(0.000)
                if 'due_discount_days' not in validated_data:
                    instance.due_discount_days = None
            if errors:
                raise serializers.ValidationError(errors)
            for field in allowed_fields:
                if field in validated_data:
                    setattr(instance, field, validated_data[field])
            instance.save()
            return instance
        elif status == 'submitted':
            # No field updates allowed except via status change
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Sunuldu durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'approved':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Onaylandı durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'rejected':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Reddedildi durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'ordered':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Sipariş verildi durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'billed':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Faturalandı durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'paid':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'Ödendi durumunda sadece status değiştirilebilir.'})
            return instance
        elif status == 'cancelled':
            non_status_updates = [field for field in allowed_fields if field in validated_data]
            if non_status_updates:
                raise serializers.ValidationError({'fields': 'İptal edildi durumunda sadece status değiştirilebilir.'})
            return instance
        else:
            raise serializers.ValidationError({'status': f"Bilinmeyen durum: {status}"})
