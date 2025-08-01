
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import StockMovement, InventoryBalance

@receiver(post_save, sender=StockMovement)
def update_inventory_balance_on_save(sender, instance, created, **kwargs):
    balance_object, _ = InventoryBalance.objects.get_or_create(
        material=instance.material,
        uom=instance.uom,
        defaults={'quantity': 0}
    )
    balance_object.quantity += instance.quantity
    balance_object.save()