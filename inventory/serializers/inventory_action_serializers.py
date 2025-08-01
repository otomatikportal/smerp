
from rest_framework import serializers
from core.fields import UOMField

from inventory.models import InventoryLocation
from core.models import Material
from django.conf import settings
from django.contrib.auth import get_user_model

class EnterFromPOLineSerializer(serializers.Serializer):
    location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all(), required=True)
    quantity = serializers.DecimalField(max_digits=30, decimal_places=2, required=True)
    reason = serializers.CharField(required=False)
    created_by = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)


class ExitFromSOLineSerializer(serializers.Serializer):
    location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all(), required=True)
    quantity = serializers.DecimalField(max_digits=30, decimal_places=2, required=True)
    reason = serializers.CharField(required=False)
    created_by = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)


class AdjustmentSerializer(serializers.Serializer):
    location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all(), required=True)
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), required=True)
    uom = serializers.ChoiceField(choices=UOMField.Unit.choices, required=True)
    new_quantity = serializers.DecimalField(max_digits=30, decimal_places=2, required=True)
    reason = serializers.CharField(required=False)
    created_by = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)

    def validate(self, attrs):
        uom = attrs.get('uom')
        new_quantity = attrs.get('new_quantity')
        if uom in ['PLT', 'BOX', 'ADT']:
            if new_quantity is not None and new_quantity % 1 != 0:
                raise serializers.ValidationError({
                    'new_quantity': 'Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.'
                })
        return attrs

class TransferSerializer(serializers.Serializer):
    from_location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all(), required=True)
    to_location = serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all(), required=True)
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), required=True)
    quantity = serializers.DecimalField(max_digits=30, decimal_places=2, required=True)
    uom = serializers.ChoiceField(choices=UOMField.Unit.choices, required=True)
    reason = serializers.CharField(required=False)
    created_by = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)

    def validate(self, attrs):
        uom = attrs.get('uom')
        quantity = attrs.get('quantity')
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise serializers.ValidationError({
                    'quantity': 'Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.'
                })
        return attrs
