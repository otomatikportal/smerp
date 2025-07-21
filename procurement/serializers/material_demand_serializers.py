from rest_framework import serializers
from procurement.models import MaterialDemand
from core.serializers.material_serializers import MaterialSerializer

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
            'deadline',
            'description',
            'status',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['demand_no', 'status', 'created_by', 'created_at']

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        action = self.context.get('action')
        material = instance.material
        if action == 'retrieve':
            ret['material'] = MaterialSerializer(material, context=self.context).data
        elif action == 'list':
            ret['material_internal_code'] = getattr(material, 'internal_code', None)
            ret['material'] = getattr(material, 'internal_code', None)
        return ret

    def create(self, validated_data):
        return MaterialDemand.objects.create(**validated_data)

    def partial_update(self, instance, validated_data):
        # Only allow updating quantity, deadline, and description
        allowed_fields = ['quantity', 'deadline', 'description']
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance

    def delete(self, instance):
        """
        Triggers the model's delete method, which should invoke the soft delete policy if using a soft delete library.
        """
        instance.delete()
        return instance
