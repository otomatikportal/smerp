from rest_framework import serializers
from core.models import Company
from core.serializers.contact_serializers import ContactSerializer

class CompanySerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)
    contacts = ContactSerializer(many=True, required=False)

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'legal_name',
            'e_mail',
            'website',
            'phone',
            'description',
            'created_by',
            'created_at',
            'contacts',
        ]
        read_only_fields = ['created_by', 'created_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        action = self.context.get('action')
        if action == 'retrieve':
            contacts_qs = instance.contacts.all()
            ret['contacts'] = ContactSerializer(contacts_qs, many=True).data
        else:
            ret.pop('contacts', None)
        return ret

    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', None)
        company = Company.objects.create(**validated_data)
        if contacts_data:
            for contact_data in contacts_data:
                contact_data['company'] = company
                ContactSerializer().create(contact_data)
        return company


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
        # Only allow updating name, legal_name, e_mail, website, phone, and description
        allowed_fields = ['name', 'legal_name', 'e_mail', 'website', 'phone', 'description']
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