from rest_framework import serializers
from core.models import Company
from core.models.material import Material

class MaterialDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name']
        read_only_fields = fields
        
class CompanyDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']
        read_only_fields = fields
        
