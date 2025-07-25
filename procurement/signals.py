from django.db.models.signals import post_save
from django.dispatch import receiver
from procurement.models import ProcurementOrder
from sales.models import VariableCost

@receiver(post_save, sender=ProcurementOrder)
def create_cost_data(sender, instance, **kwargs):
    # Only act if status is 'approved'
    if instance.status == 'approved':
        for line in instance.lines.all():
            # Only create if this material-procurement_order combo does not exist
            if not VariableCost.objects.filter(procurement_order=instance, material=line.material).exists():
                VariableCost.objects.create(
                    procurement_order=instance,
                    material=line.material,
                    cost=line.unit_price,
                    uom=line.uom
                )
