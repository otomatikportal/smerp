from rest_framework import serializers
from core.models import Contact

class ContactSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id',
            'company',
            'name',
            'last_name',
            'gender',
            'role',
            'e_mail',
            'phone',
            'description',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']

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
        allowed_fields = ['name', 'last_name', 'gender', 'role', 'e_mail', 'phone', 'description']
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
