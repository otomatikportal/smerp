from django.contrib.auth.models import User
from django.db import models
from jsonschema import ValidationError
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from core.fields import UOMField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from procurement.models import ProcurementOrderLine
import decimal
from sales.models import SalesOrderLine
from inventory.models import InventoryLocation


class StockMovement(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    
    class Action(models.TextChoices):
        IN = "IN", _("Depoya giriş")
        OUT = "OUT", _("Depodan çıkış")
        ADJUST = "ADJUST", _("Adjustment")
        TRANSFER = "TRANSFER", _("Transfer")

    material =   models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.PROTECT, null=False, blank=False)
    uom =        UOMField()
    quantity =   models.DecimalField(_("Miktar"), max_digits=30, decimal_places=2, null=False, blank=False)
    location =   models.ForeignKey("inventory.InventoryLocation", verbose_name=_("Konum"), on_delete=models.PROTECT)
    action =     models.CharField(max_length=16,choices=Action.choices,verbose_name=_("Eylem"),null=False,blank=False)
    unit_cost =  models.DecimalField(_("Birim fiyat"), max_digits=30, decimal_places=2)
    po_line =    models.ForeignKey("procurement.ProcurementOrder", verbose_name=_("PO#"), on_delete=models.CASCADE,null=True, blank=True, default=None)
    so_line =    models.ForeignKey("sales.SalesOrder", verbose_name=_("SO#"), on_delete=models.CASCADE,null=True, blank=True, default=None)
    reason =     models.TextField(_("Gerekçe"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Oluşturuldu"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Oluşturan"))

    class Meta:
        permissions = [
            ("transact_stockrecord", "Enter/exit stock, see incoming and exits"),
        ]
        verbose_name = _("Stock Record")
        verbose_name_plural = _("Stock Records")
        
    @property
    def po(self):
        """Return the related PO object via po_line, or None if not set."""
        return self.po_line.po if self.po_line and hasattr(self.po_line, 'po') else None

    @property
    def so(self):
        """Return the related SO object via so_line, or None if not set."""
        return self.so_line.so if self.so_line and hasattr(self.so_line, 'so') else None
    
    @classmethod
    def enter_from_po_line(
        cls,
        po_line: ProcurementOrderLine,
        target_location: InventoryLocation,
        created_by: User,
        quantity: decimal.Decimal,
        reason: str
    ):
        if quantity <= 0:
            raise ValidationError(_("Girişlerde miktar pozitif olmalıdır."))
        
        return cls.objects.create(
            location=target_location,
            material=po_line.material,
            quantity=quantity,
            unit_cost=po_line.unit_price,
            created_by=created_by,
            po_line=po_line,
            reason=reason,
            action=cls.Action.IN
        )
        
    @classmethod
    def exit_from_so_line(
        cls,
        so_line: SalesOrderLine,
        quantity: decimal.Decimal,
        location: InventoryLocation,  
    ):
    
        if quantity <= 0:
            raise ValidationError(_('Miktar pozitif olmalıdır'))
        
        material = so_line.material
        uom = so_line.uom
        
        deductible_records = cls.objects.filter(location=location, material=material, uom=uom)
        available_qty = deductible_records.aggregate(total=models.Sum('quantity'))['total'] or 0

        if not deductible_records.exists():
            raise ValidationError(_('Verilen konumda bu malzeme bu birimle mevcut değil'))

        if quantity > available_qty:
            raise ValidationError(_('Bu depolama bölgesinde bu miktarda malzeme yok'))

        # Weighted average unit_cost calculation
        total_cost = sum(float(rec.unit_cost) * float(rec.quantity) for rec in deductible_records)
        weighted_avg_cost = (total_cost / available_qty)
        
        return cls.objects.create(
            material=material,
            uom=uom,
            quantity=-abs(so_line.quantity),
            location=location,
            so_line=so_line,
            action=cls.Action.OUT,
            unit_cost=weighted_avg_cost
        )