from rest_framework import serializers
from core.models import Material

class MaterialSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Material
        fields = [
            'id',
            'name',
            'category',
            'internal_code',
            'description',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['internal_code', 'created_by', 'created_at']

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
        # Only allow updating name and description
        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'description' in validated_data:
            instance.description = validated_data['description']
        instance.save()
        return instance

    def delete(self, instance):
        """
        Triggers the model's delete method, which should invoke the soft delete policy if using a soft delete library.
        """
        instance.delete()
        return instance
