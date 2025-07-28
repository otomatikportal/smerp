from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import Bom, BomLine


def create_variable_cost_for_bom_instance(bom_instance):
    VariableCost = apps.get_model('sales', 'VariableCost')
    latest_cost = bom_instance.latest_cost
    
    # Only create VariableCost if latest_cost is not None and not zero
    if latest_cost is not None and latest_cost > 0:
        reference_cost = VariableCost.objects.filter(
            material=bom_instance.product
        ).order_by('-id').first()
        
        if reference_cost:
            currency = getattr(reference_cost, 'currency', 'TRY')
        else:
            currency = 'TRY'
        
        VariableCost.objects.create(
            bom=bom_instance,
            material=bom_instance.product,
            cost=latest_cost,
            currency=currency,
            uom=bom_instance.uom
        )


@receiver(post_save, sender=Bom)
def create_variable_cost_from_bom(sender, instance, created, **kwargs):
    # Only trigger for updates, not creation (creation is handled by serializer)
    if not created:
        create_variable_cost_for_bom_instance(instance)


@receiver(post_save, sender=BomLine)
def create_variable_cost_from_bomline(sender, instance, created, **kwargs):
    create_variable_cost_for_bom_instance(instance.bom)
