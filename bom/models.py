from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from core.fields import UOMField

from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Bom(SafeDeleteModel):

    _safedelete_policy = SOFT_DELETE
    product = models.OneToOneField('core.Material', on_delete=models.CASCADE, related_name='bom', null=False, blank=False)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    machining_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    history = HistoricalRecords()
    
    @property
    def latest_cost(self):
        """
        Calculates the total latest cost of all components in the BOM using VariableCost records 
        that match the UOM specified in each BOM line.
        Returns None if any component has no cost for the required UOM.
        """
        total = 0
        
        for line in self.lines.all():
            # Get the latest cost for this material with matching UOM
            material_cost = line.component.latest_cost_for_uom(line.uom)
            
            if material_cost is None:
                return None
            
            total += material_cost * line.quantity
        
        return total
    
    def __str__(self):
        return f"BOM for {self.product.name}"
    
    def clean(self):
        # Prevent the product from being used as a component in any of its lines
        if self.pk and self.lines.filter(component=self.product).exists():
            raise ValidationError(_("Bir Reçete'nin ürünü, kendi Reçete satırlarında bileşen olarak kullanılamaz."))

class BomLine(SafeDeleteModel):

    _safedelete_policy = SOFT_DELETE
    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name='lines', null=False, blank=False)
    component = models.ForeignKey('core.Material', on_delete=models.CASCADE, null=False, blank=False)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], null=False, blank=False)
    uom = UOMField(null=False, blank=False, default=None)
    history = HistoricalRecords()
    
    class Meta:
        unique_together = ['bom', 'component']
    
    def __str__(self):
        return f"{self.component.name} x {self.quantity} {self.uom}"
    
    def clean(self):
        # Prevent the component from being the same as the BOM's product
        if self.bom and self.component == self.bom.product:
            raise ValidationError(_("Bir Reçete satırının bileşeni, Reçete'nin ürünü ile aynı olamaz."))

        # Prevent circularity: component cannot (directly or indirectly) be the parent product
        # Traverse up the BOM tree from the component
        visited = set()
        current_material = self.component
        while True:
            if current_material == self.bom.product:
                raise ValidationError(_("Döngüsel Reçete ilişkisi: Bu bileşen, Reçete'nin ürünü ile dolaylı olarak aynı olamaz."))
            # If the material has a BOM, go up to its product
            bom = getattr(current_material, 'bom', None)
            if not bom or not hasattr(bom, 'product'):
                break
            # Prevent infinite loop in case of corrupted data
            if current_material.pk in visited:
                break
            visited.add(current_material.pk)
            current_material = bom.product