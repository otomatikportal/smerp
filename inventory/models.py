from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from simple_history.models import HistoricalRecords
from core.fields import GenderField, CurrencyField, UOMField
from django.utils.translation import gettext_lazy as _

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
    
    
class StockRecord(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    material =           models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.PROTECT, null=False, blank=False)
    uom =                UOMField()
    quantity =           models.DecimalField(_("Miktar"), max_digits=30, decimal_places=2, null=False, blank=False)
    location =           models.ForeignKey("inventory.InventoryLocation", verbose_name=_("Konum"), on_delete=models.PROTECT)
    history =            HistoricalRecords()

    class Meta:
        unique_together = ("material", "uom", "location")
        
        permissions = [
            ("transact_stockrecord", "Enter/exit stock"),
        ]