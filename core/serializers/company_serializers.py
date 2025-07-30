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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        view = self.context.get('view')
        if view is not None:
            action = getattr(view, 'action', None)
        else:
            action = None

        print(action)
        
        if action == 'retrieve':
            ret['contacts'] = ContactSerializer(instance.contacts.all(), many=True).data
            
        elif action == 'list':
            ret['contacts_count'] = instance.contacts.count()
            ret.pop('contacts', None)
        else:
            ret.pop('contacts', None)

        return ret

    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', [])
        company = Company.objects.create(**validated_data)
        
        for contact_data in contacts_data:
            contact_data['company'] = company.pk
            contact_serializer = ContactSerializer(data=contact_data)
            if contact_serializer.is_valid(raise_exception=True):
                contact_serializer.save()
        
        return company
    
    def update(self, instance, validated_data):
        validated_data.pop('contacts', None)
        return super().update(instance, validated_data)


