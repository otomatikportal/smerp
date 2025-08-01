from rest_framework import serializers
from sales.models import SalesOrder
from sales.serializers.sales_order_line_serializers import SalesOrderLineSerializer


class SalesOrderSerializer(serializers.ModelSerializer):
    count_of_lines = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    lines = SalesOrderLineSerializer(many=True, required=False)
    
    class Meta:
        model = SalesOrder
        fields = [
            'so_number',
            'customer',
            'customer_name',
            'payment_term',
            'payment_method',
            'incoterms',
            'trade_discount',
            'due_in_days',
            'due_discount_days',
            'invoice_date',
            'invoice_number',
            'description',
            'currency',
            'delivery_address',
            'dispatch_ordered',
            'total_price_without_tax',
            'total_price_with_tax',
            'all_sent',
            'invoice_accepted',
            'last_payment_date',
            'status',
            'created_by',
            'created_at',
            'count_of_lines',
            'lines'
        ]
        read_only_fields = [
            'so_number',
            'customer_name',
            'total_price_without_tax',
            'total_price_with_tax',
            'all_sent',
            'invoice_accepted',
            'last_payment_date',
            'status',
            'created_by',
            'created_at',
        ]

    def get_count_of_lines(self, obj):
        return obj.lines.count() if hasattr(obj, 'lines') else 0

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
    

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', None)
        sales_order = SalesOrder.objects.create(**validated_data)

        if lines_data:
            for line_data in lines_data:
                line_data['so'] = sales_order
                SalesOrderLineSerializer().create(line_data)

        return sales_order

    def update(self, instance, validated_data):
        
        if instance.status != 'draft':
            raise serializers.ValidationError({
                'status': f"SO cannot be updated because its status is '{instance.status}'. Only 'draft' SOs can be edited."
            })
            
        allowed_fields = [
            'customer', 'payment_term', 'payment_method', 'incoterms', 'trade_discount',
            'due_in_days', 'due_discount_days', 'invoice_date', 'invoice_number',
            'description', 'currency', 'delivery_address'
        ]

        disallowed = [field for field in validated_data if field not in allowed_fields]
        if disallowed:
            raise serializers.ValidationError({
                'fields': f"Only the following fields can be updated in a draft SO: {', '.join(allowed_fields)}. "
                          f"You tried to update: {', '.join(disallowed)}"
            })

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        view = self.context.get('view')
        action = getattr(view, 'action', None)

        if action == 'retrieve':
            child_context = {**self.context, 'action': 'list'}
            ret['lines'] = SalesOrderLineSerializer(
                instance.lines.all(),
                many=True,
                context=child_context
            ).data

        elif action == 'list':
            ret['count_of_lines'] = self.get_count_of_lines(instance)
            ret.pop('lines', None)  # Remove lines list

        return ret