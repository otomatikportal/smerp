from xml.dom import ValidationErr
from django.contrib.auth.models import User
from django.db import models
from jsonschema import ValidationError
from pytz import timezone
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from simple_history.models import HistoricalRecords
from core.fields import GenderField, CurrencyField, UOMField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from procurement.models import ProcurementOrderLine
import decimal

from sales.models import SalesOrderLine

class InventoryLocation(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    class Meta:
        unique_together = ("facility", "area", "section", "shelf", "bin")

    class Facility(models.TextChoices):
        ESENYURT   = "esenyurt", _("Esenyurt")
        
    class Type(models.TextChoices):
        INDUSTRIAL_SHELF =      "industrial_shelf", _("Raf")        
        EXIT_TRANSIT =          "exit_transit", _("Sevk transit")
        INJECTION_TRANSIT =     "injection_transit", _("Enjeksiyondan depoya")
        MANUFACTURING_TRANSIT = "manufacturing_transit", _("Montajdan depoya")
        RESIN =                 "resin_storage", _("Plastik hammadde")
        MASTERBATCH =           "masterbatch", _("Masterbatch")
        CHEMICAL =              "chemical", _("Kimyasal")
        UNLABELED =             "unlabeled", _("Bildirilmemiş")
        TEMP =                  "temporary", _("Geçici")

    name =     models.CharField(_("İsim"), max_length=50, blank=True)
    facility = models.CharField(_("Tesis"), max_length=50, choices=Facility.choices, default=Facility.ESENYURT)
    area =     models.IntegerField(_("Bölge"), null=True, blank=False)
    section =  models.IntegerField(_("Sıra"), null=True, blank=False)
    shelf =    models.IntegerField(_("Raf"), null=True, blank=False)
    bin =      models.IntegerField(_("Bölme"), null=True, blank=False)
    type =     models.CharField(_("Tipi"), max_length=50, choices=Type.choices, default=Type.UNLABELED)
    width =    models.IntegerField(_("Genişliği (cm)"), null=True, blank=False)
    height =   models.IntegerField(_("Yüksekliği (cm)"), null=True, blank=False)
    depth =    models.IntegerField(_("Derinlik (cm)"), null=True, blank=False)
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        # Only assign auto-generated name if all unique_together fields are present
        unique_fields = [self.facility, self.area, self.section, self.shelf, self.bin]
        if all(field is not None for field in unique_fields):
            area_str = chr(65 + (self.area - 1)) if self.area is not None and self.area > 0 else "A"
            section_str = str(self.section) if self.section is not None else "1"
            base = f"{area_str}{section_str}"
            if self.shelf == 0:
                middle = "Z"
            else:
                middle = f"R{self.shelf}"
            end = f"-P{self.bin}" if self.bin is not None else ""
            self.name = f"{base}-{middle}{end}"
        super().save(*args, **kwargs)
        
    @classmethod
    def generate_name(cls, facility, area, section, shelf, bin):
        """
        Generate a consistent name based on facility, area, section, shelf, and bin.
        Matches the logic in save().
        
        Args:
            facility (str): Facility code (e.g., 'esenyurt')
            area (int): Area number (1+)
            section (int): Section number
            shelf (int): Shelf number (0 means 'Z')
            bin (int): Bin number

        Returns:
            str: Generated name (e.g., "A1-R1-P2", "B3-Z-P0")
        """
        # Only generate if all required fields are present
        if not all(v is not None for v in [facility, area, section, shelf, bin]):
            return ""

        try:
            area_str = chr(65 + (area - 1)) if area >= 1 else "X"
            section_str = str(section)
            base = f"{area_str}{section_str}"
            middle = "Z" if shelf == 0 else f"R{shelf}"
            end = f"-P{bin}"

            return f"{base}-{middle}{end}"
        except (ValueError, TypeError, OverflowError):
            return ""
    
    
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
        
        
        
        
        
        
        
        
        
