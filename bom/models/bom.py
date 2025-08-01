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
    uom = UOMField(null=False, blank=False, default=None)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    machining_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    history = HistoricalRecords()
    
    class Meta:
        unique_together = ['product', 'uom']
        
    
    @property
    def latest_cost(self):
        """
        Calculates the total latest cost of all components in the BOM using VariableCost records 
        that match the UOM specified in each BOM line.
        Returns None if any component has no cost for the required UOM, if labor_cost or machining_cost is missing,
        or if the BOM has no lines.
        """
        if self.labor_cost is None or self.machining_cost is None:
            return None
            
        lines = self.lines.all()
        
        # Return None if BOM has no lines
        if not lines.exists():
            return None
            
        total = 0
        
        for line in lines:
            # Get the latest cost for this material with matching UOM
            material_cost = line.component.latest_cost_for_uom(line.uom)
            
            if material_cost is None:
                return None
            
            total += material_cost * line.quantity
        
        return total + self.labor_cost + self.machining_cost
    
    def __str__(self):
        return f"BOM for {self.product.name}"
    
    def clean(self):
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
        unique_together = ['bom', 'component', 'uom']
    
    def __str__(self):
        return f"{self.component.name} x {self.quantity} {self.uom}"
    
    def clean(self):
        if self.pk:
            original = self.__class__.objects.get(pk=self.pk)
            if original.bom != self.bom:
                raise ValidationError(_("BOM alanı oluşturulduktan sonra değiştirilemez."))
        
        if self.bom and self.component == self.bom.product:
            raise ValidationError(_("Bir Reçete satırının bileşeni, Reçete'nin ürünü ile aynı olamaz."))

        visited = set()
        current_material = self.component
        while True:
            if current_material == self.bom.product:
                raise ValidationError(_("Döngüsel Reçete ilişkisi: Bu bileşen, Reçete'nin ürünü ile dolaylı olarak aynı olamaz."))
            bom = getattr(current_material, 'bom', None)
            if not bom or not hasattr(bom, 'product'):
                break
            if current_material.pk in visited:
                break
            visited.add(current_material.pk)
            current_material = bom.product