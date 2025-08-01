from django.contrib.auth.models import User
from django.db import models
from core.fields import UOMField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from procurement.models import ProcurementOrderLine
import decimal
from sales.models import SalesOrderLine
from inventory.models import InventoryLocation
from core.models import Material
from rest_framework.exceptions import ValidationError
from django.db import transaction

class InventoryBalance(models.Model):
    material = models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.CASCADE, null=False, blank=False)
    quantity = models.DecimalField(_("Miktar"), max_digits=30, decimal_places=2)
    uom = UOMField(null=False, blank=False)

class StockMovement(models.Model):
    class Action(models.TextChoices):
        IN = "IN", _("Depoya giriş")
        OUT = "OUT", _("Depodan çıkış")
        ADJUST = "ADJUST", _("Adjustment")
        TRANSFER = "TRANSFER", _("Transfer")
        MO_IN = "MO_IN", _('Üretimden gelen')
        MO_OUT = "MO_UT", _('Üretime giden')

    material =   models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.PROTECT, null=False, blank=False)
    uom =        UOMField()
    quantity =   models.DecimalField(_("Miktar"), max_digits=30, decimal_places=2, null=False, blank=False)
    location =   models.ForeignKey("inventory.InventoryLocation", verbose_name=_("Konum"), on_delete=models.PROTECT)
    action =     models.CharField(max_length=16,choices=Action.choices,verbose_name=_("Eylem"),null=False,blank=False)
    unit_cost =  models.DecimalField(_("Birim fiyat"), max_digits=30, decimal_places=2)
    po_line =    models.ForeignKey("procurement.ProcurementOrderLine", verbose_name=_("PO#"), on_delete=models.CASCADE,null=True, blank=True, default=None)
    so_line =    models.ForeignKey("sales.SalesOrderLine", verbose_name=_("SO#"), on_delete=models.CASCADE,null=True, blank=True, default=None)
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
    @transaction.atomic
    def enter_from_po_line(
        cls,
        po_line: ProcurementOrderLine,
        location: InventoryLocation,
        quantity: decimal.Decimal,
        reason: str,
        created_by: User,
    ):
        uom = getattr(po_line, 'uom', None)
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise ValidationError({'quantity': _('Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.')})
        if quantity <= 0:
            raise ValidationError(_("Girişlerde miktar pozitif olmalıdır."))
        if quantity > po_line.quantity_left:
            raise ValidationError(_('Alış emrinde kalandan fazla miktar girilemez.'))
        po_line._history_user = created_by #type: ignore
        po_line.quantity_received += quantity
        po_line.save()
        return cls.objects.create(
            location=location,
            material=po_line.material,
            quantity=quantity,
            unit_cost=po_line.unit_price,
            created_by=created_by,
            reason=reason,
            po_line=po_line,
            action=cls.Action.IN
        )
        
        
     
    @classmethod
    @transaction.atomic
    def exit_from_so_line(
        cls,
        so_line: SalesOrderLine,
        quantity: decimal.Decimal,
        location: InventoryLocation,
        reason: str,
        created_by: User
    ):
        uom = getattr(so_line, 'uom', None)
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise ValidationError({'quantity': _('Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.')})
        if quantity <= 0:
            raise ValidationError(_('Miktar pozitif olmalıdır'))
        if quantity > so_line.quantity_left:
            raise ValidationError(_('Gönderilecek miktar satışta kalandan fazla olamaz'))
        material = so_line.material
        uom = so_line.uom
        deductible_records = cls.objects.filter(location=location, material=material, uom=uom)
        available_qty = deductible_records.aggregate(total=models.Sum('quantity'))['total'] or 0
        if not deductible_records.exists():
            raise ValidationError(_('Verilen konumda bu malzeme bu birimle mevcut değil'))
        if quantity > available_qty:
            raise ValidationError(_('Bu depolama bölgesinde bu miktarda malzeme yok'))
        positive_records = [rec for rec in deductible_records if rec.quantity > 0]
        positive_qty = sum(float(rec.quantity) for rec in positive_records)
        total_cost = sum(float(rec.unit_cost) * float(rec.quantity) for rec in positive_records)
        weighted_avg_cost = (total_cost / positive_qty) if positive_qty else 0
        so_line._history_user = created_by #type: ignore
        so_line.quantity_sent += quantity
        so_line.save()
        return cls.objects.create(
            material=material,
            uom=uom,
            quantity=-abs(so_line.quantity),
            location=location,
            so_line=so_line,
            action=cls.Action.OUT,
            unit_cost=weighted_avg_cost,
            reason=reason,
            created_by=created_by
        )
        
        
       
    @classmethod
    @transaction.atomic
    def adjustment(
        cls,
        location: InventoryLocation,
        material: Material,
        uom,
        new_quantity: decimal.Decimal,
        reason: str,
        created_by: User
    ):
        if uom in ['PLT', 'BOX', 'ADT']:
            if new_quantity is not None and new_quantity % 1 != 0:
                raise ValidationError({'quantity': _('Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.')})
        if uom is None:
            raise ValidationError(_('Birim (UOM) boş olamaz!'))
        if location is None:
            raise ValidationError(_('Konum boş olamaz!'))
        if material is None:
            raise ValidationError(_('Malzeme boş olamaz!'))
        if new_quantity < 0:
            raise ValidationError(_('Yeni miktar 0 dan az olamaz!'))
        records = cls.objects.filter(location=location, material=material, uom=uom)
        positive_records = [rec for rec in records if rec.quantity > 0]
        positive_qty = sum(float(rec.quantity) for rec in positive_records)
        total_cost = sum(float(rec.unit_cost) * float(rec.quantity) for rec in positive_records)
        weighted_avg_cost = (total_cost / positive_qty) if positive_qty else 0
        available_qty = records.aggregate(total=models.Sum('quantity'))['total'] or 0
        shared_fields = {
            "uom": uom,
            "location": location,
            "unit_cost": weighted_avg_cost,
            "action": cls.Action.ADJUST,
            "reason": reason,
            "created_by": created_by
        }
        if new_quantity == 0:
            return cls.objects.create(
                quantity = -abs(available_qty),
                **shared_fields
            )
        if new_quantity < available_qty:
            deduction = available_qty - new_quantity
            return cls.objects.create(
                quantity = -abs(deduction),
                **shared_fields
            )
        if new_quantity > available_qty:
            addition = new_quantity - available_qty
            return cls.objects.create(
                quantity = addition,
                **shared_fields
            )
            
         
    @classmethod
    @transaction.atomic
    def transfer(
        cls,
        from_location: InventoryLocation,
        to_location: InventoryLocation,
        material: Material,
        quantity: decimal.Decimal,
        uom,
        reason: str,
        created_by: User,
    ):
        if uom in ['PLT', 'BOX', 'ADT']:
            if quantity is not None and quantity % 1 != 0:
                raise ValidationError({'quantity': _('Miktar, Palet, Koli veya Adet birimleri için tam sayı olmalıdır.')})
        records = cls.objects.filter(location=from_location, material=material, uom=uom)
        available_qty = records.aggregate(total=models.Sum('quantity'))['total'] or 0 
        if quantity > available_qty:
            raise ValidationError(_('Transfer edilmeye çalışılan miktar mevcudu aşıyor'))
        positive_records = [rec for rec in records if rec.quantity > 0]
        positive_qty = sum(float(rec.quantity) for rec in positive_records)
        total_cost = sum(float(rec.unit_cost) * float(rec.quantity) for rec in positive_records)
        weighted_avg_cost = (total_cost / positive_qty) if positive_qty else 0
        shared_fields = {
            "uom": uom,
            "material": material,
            "reason": reason,
            "created_by": created_by,
            "action": cls.Action.TRANSFER,
            "unit_cost": weighted_avg_cost
        }
        cls.objects.create(
            **shared_fields,
            quantity = -abs(quantity),
            location = from_location
        )
        return cls.objects.create(
            **shared_fields,
            quantity = abs(quantity),
            location = to_location
        )