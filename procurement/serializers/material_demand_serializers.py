from rest_framework import serializers
from procurement.models import MaterialDemand

class MaterialDemandSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MaterialDemand
        fields = [
            'id',
            'demand_no',
            'material',
            'quantity',
            'uom',
            'history',
            'deadline',
            'description',
            'status',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['demand_no', 'status', 'history', 'created_by', 'created_at']

    def get_created_by(self, obj):
        # Use django-simple-history to get the first history record's user
        first_history = obj.history.order_by('history_date').first()
        if first_history and hasattr(first_history, 'history_user') and first_history.history_user:
            return str(first_history.history_user)
        return None

    def get_created_at(self, obj):
        # Use django-simple-history to get the first history record's date
        first_history = obj.history.order_by('history_date').first()
        if first_history:
            return first_history.history_date
        return None

    def create(self, validated_data):
        return MaterialDemand.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Only allow updating quantity, deadline, and description (comment)
        for attr in ['quantity', 'deadline', 'description']:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()
        return instance
