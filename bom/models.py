from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from core.fields import UOMField
from simple_history.models import HistoricalRecords

class Bom(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    product = models.OneToOneField('core.Material', on_delete=models.CASCADE, related_name='bom')
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    machining_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    history = HistoricalRecords()
    
    def __str__(self):
        return f"BOM for {self.product.name}"

class BomLine(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name='lines')
    component = models.ForeignKey('core.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal(1.00))
    uom = UOMField()
    history = HistoricalRecords()
    
    class Meta:
        unique_together = ['bom', 'component']
    
    def __str__(self):
        return f"{self.component.name} x {self.quantity} {self.uom}"