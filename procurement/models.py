from django.db import models
from simple_history.models import HistoricalRecords
from core.fields import CurrencyField, UOMField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE, SOFT_DELETE_CASCADE
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, date
    
class MaterialDemand(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    STATUS = [
        ("submitted", "Gönderildi"),
        ("approved", "Onaylandı"),
        ("closed", "Kapandı"),
    ]
    
    demand_no = models.CharField(_('Talep No'), max_length=50, blank=True, null=True, unique=True)
    material = models.ForeignKey("core.Material", related_name='demands' ,on_delete=models.PROTECT, null=False, blank=False, verbose_name=_('Malzeme'))
    quantity = models.DecimalField(_('Miktar'), max_digits=12, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(Decimal('0.00'))])
    uom = UOMField()
    deadline = models.DateField(_('Son Tarih'), auto_now=False, auto_now_add=False)
    description = models.TextField(_('Açıklama'), max_length=500)
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS, default="draft")
    history = HistoricalRecords()
    
    def __str__(self):
        return str(self.demand_no)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        
        if creating and not self.demand_no:
            prefix = "#"
            year = str(datetime.now().year)[-2:]
            pk_str = str(self.pk)
            zeros_len = 14 - (len(prefix) + len(year) + len(pk_str))
            zeros = '0' * max(0, zeros_len)
            self.demand_no = f"{prefix}{year}{zeros}{pk_str}"[:14]
            super().save(update_fields=["demand_no"])
            

            

class ProcurementOrder(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE
    
    PAYMENT_TERMS = [
        ("NET_T", "Net Vade"),
        ("DUE_ON_RECEIPT", "Teslimde Ödeme"),
        ("CIA", "Peşin Ödeme"),
        ("COD", "Teslimde Nakit"),
        ("EOM", "Ay Sonu"),
        ("PARTIAL_ADVANCE", "Kısmi Peşin Ödeme"),
        ("LC", "Akreditif"),
        ("TRADE_DISCOUNT", "Ticari İskonto"),
    ]
    
    INCOTERMS = [
        ("EXW", "İşyerinde Teslim (EXW)"),
        ("FCA", "Taşıyıcıya Teslim (FCA)"),
        ("FAS", "Gemi Yanında Teslim (FAS)"),
        ("FOB", "Gemiye Teslim (FOB)"),
        ("CFR", "Navlun Dahil Teslim (CFR)"),
        ("CIF", "Navlun ve Sigorta Dahil Teslim (CIF)"),
        ("CPT", "Taşıma Ücreti Ödenmiş Teslim (CPT)"),
        ("CIP", "Taşıma ve Sigorta Ücreti Ödenmiş Teslim (CIP)"),
        ("DAP", "Varış Yerinde Teslim (DAP)"),
        ("DPU", "Boşaltılmış Teslim (DPU)"),
        ("DDP", "Gümrük Vergisi Ödenmiş Teslim (DDP)"),
    ]
    
    PAYMENT_METHODS = [
        ("BANK_TRANSFER", "Banka Havalesi"),
        ("CASH", "Nakit"),
        ("CREDIT_CARD", "Kredi Kartı"),
        ("CHEQUE", "Çek"),
        ("EFT", "EFT"),
        ("PROMISSORY_NOTE", "Senet"),
        ("OTHER", "Diğer")
    ]
    
    STATUS = [
        ('draft', 'Taslak'),
        ('submitted', 'Sunuldu'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi'),
        ('ordered', 'Sipariş verildi'),
        ('billed', 'Faturalandı'),
        ('paid', 'Ödendi'),
        ('cancelled', 'İptal edildi')
    ]
    
    po_number = models.CharField(_("PO #no"), max_length=50, unique=True, null=True, blank=False)
    vendor = models.ForeignKey("core.Company", on_delete=models.CASCADE, blank=False, null=True, verbose_name=_('Tedarikçi'))
    payment_term = models.CharField(_('Ödeme Koşulları'), max_length=20, choices=PAYMENT_TERMS)
    payment_method = models.CharField(_('Ödeme Yöntemi'), max_length=20, choices=PAYMENT_METHODS)
    incoterms = models.CharField(_('Teslim Şekli (Incoterms)'), max_length=20, choices=INCOTERMS)
    trade_discount = models.DecimalField(_('Ticari İskonto'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_in_days = models.DurationField(_('Vade Günü'))
    due_discount = models.DecimalField(_('Vade İskontosu'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_discount_days = models.DurationField(_('Vade İskonto Günü'), null=True, blank=False)
    invoice_date =  models.DateField(_('Fatura Tebliğ Tarihi'), null=True, blank=False)
    description = models.TextField(_('Açıklama'), max_length=500)
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS, default="draft") 
    currency = CurrencyField(null=False, blank=False)
    delivery_address = models.CharField(_('Teslimat Adresi'), max_length=250, null=True, blank=False)
    history = HistoricalRecords()
    
    def __str__(self):
        return str(self.po_number)
    
    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        
        if creating and not self.po_number:
            prefix = "PO-#"
            year = str(datetime.now().year)[-2:]
            pk_str = str(self.pk)
            zeros_len = 16 - (len(prefix) + len(year) + len(pk_str))
            zeros = '0' * max(0, zeros_len)
            self.po_number = f"{prefix}{year}{zeros}{pk_str}"[:16]
            super().save(update_fields=["po_number"])
    

    class Meta:
        permissions = [
            ("submit_procurementorder", "Procurement officer approval"),
            ("approve_procurementorder", "Procurement manager approval"),
            ("order_procurementorder", "Procurement order permission"),
            ("cancel_procurementorder", "Procurement order cancel permission"),
            ("bill_procurementorder", "Can set invoice issuance date, also means invoice is approved"),
        ]
    
    @property
    def total_price_without_tax(self):
        # Sum of unit_price * quantity for all lines, minus trade_discount and due_discount
        subtotal = sum(
            (line.unit_price * line.quantity)
            for line in self.lines.all() # type: ignore
            if line.unit_price is not None and line.quantity is not None
        )
        discount = subtotal * (self.trade_discount + self.due_discount)
        return subtotal - discount

    @property
    def total_price_with_tax(self):
        # Sum of (unit_price * quantity) * (1 + tax_rate) for all lines, minus discounts
        subtotal = sum(
            (line.unit_price * line.quantity)
            for line in self.lines.all() # type: ignore
            if line.unit_price is not None and line.quantity is not None
        )
        discount = subtotal * (self.trade_discount + self.due_discount)
        subtotal_after_discount = subtotal - discount
        tax_total = sum(
            (line.unit_price * line.quantity * line.tax_rate)
            for line in self.lines.all() # type: ignore
            if line.unit_price is not None and line.quantity is not None and line.tax_rate is not None
        )
        return subtotal_after_discount + tax_total

    @property
    def all_received(self):
        """Returns True if all order lines have no missing quantity (quantity_left <= 0)."""
        return all(line.quantity_left <= 0 for line in self.lines.all()) # type: ignore
    
    @property
    def invoice_accepted(self):
        """Returns True if invoice_date is present (not None)."""
        return self.invoice_date is not None
    
    @property
    def last_payment_date(self):
        if not self.invoice_date:
            return None
        term = self.payment_term
        base_date = self.invoice_date
        due_days = self.due_in_days.days if self.due_in_days else 0

        def month_end(d):
            next_month = d.replace(day=28) + timedelta(days=4)
            return next_month - timedelta(days=next_month.day)

        if term == "EOM":
            return month_end(base_date)
        elif term == "NET_T":
            return base_date + timedelta(days=due_days)
        elif term == "PARTIAL_ADVANCE":
            return base_date + timedelta(days=due_days)
        else:
            return None
    
    def can_transition_to(self, new_status, user=None):
        """Check if transition to new_status is allowed from current status"""
        transitions = {
            'draft': ['submitted'],
            'submitted': ['approved', 'rejected', 'cancelled', 'draft'],
            'approved': ['ordered', 'rejected', 'cancelled'],
            'rejected': ['draft'],
            'ordered': ['billed', 'cancelled'],
            'billed': ['paid'],
            'paid': [],
            'cancelled': []
        }
        
        return new_status in transitions.get(self.status, [])

    def validate_status_requirements(self, new_status):
        """Validate business rules for status transition"""
        errors = {}
        
        if new_status == 'submitted':
            if self.lines.count() <= 0:
                errors['lines'] = _('Satın almanın içinde malzeme yok')
            
            # Check for missing unit_price in any line
            missing_price_lines = [line for line in self.lines.all() if line.unit_price is None]
            if missing_price_lines:
                errors['lines'] = _('Satırların bir veya daha fazlasında birim fiyat eksik.')
            
            required_fields = ['payment_term', 'vendor', 'payment_method', 'incoterms', 'description', 'currency', 'delivery_address']
            for field in required_fields:
                if not getattr(self, field, None):
                    errors[field] = _("'%(field)s' alanı gereklidir.") % {'field': field}

            if self.payment_term in ['NET_T', 'PARTIAL_ADVANCE']:
                if not getattr(self, 'due_in_days', None):
                    errors['due_in_days'] = _('Bu vade tipi için vade günü gereklidir.')
        
        elif new_status == 'billed':
            if not getattr(self, 'invoice_date', None):
                errors['invoice_date'] = _("Faturalandı durumunda 'invoice_date' alanı gereklidir.")
        
        return errors

    def change_status(self, new_status, user=None, **kwargs):
        """Safely change status with all validations"""
        # Check if transition is allowed
        if not self.can_transition_to(new_status, user):
            current_display = dict(self.STATUS).get(self.status, self.status)
            new_display = dict(self.STATUS).get(new_status, new_status)
            raise ValidationError(_("%(current)s durumundan %(new)s durumuna geçiş yapılamaz") % {
                'current': current_display, 
                'new': new_display
            })
        
        # Validate business requirements
        errors = self.validate_status_requirements(new_status)
        if errors:
            raise ValidationError(errors)
        
        # Handle special cases
        if new_status == 'billed' and 'invoice_date' in kwargs:
            self.invoice_date = kwargs['invoice_date']
        
        # Change status and save
        self.status = new_status
        self.save()
        
        return self

    def get_allowed_transitions(self, user=None):
        """Get list of allowed status transitions for current user"""
        transitions = {
            'draft': ['submitted'],
            'submitted': ['approved', 'rejected', 'cancelled', 'draft'],
            'approved': ['ordered', 'rejected', 'cancelled'],
            'rejected': ['draft'],
            'ordered': ['billed', 'cancelled'],
            'billed': ['paid'],
            'paid': [],
            'cancelled': []
        }
        
        return transitions.get(self.status, [])
    
class ProcurementInvoice(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    invoice_number = models.CharField(_('Fatura No'), max_length=50, null=False, blank=False)
    po = models.ForeignKey("procurement.ProcurementOrder", related_name='invoices', on_delete=models.CASCADE, verbose_name=_('Satınalma Siparişi'))
    
class ProcurementOrderLine(SafeDeleteModel):

    _safedelete_policy = SOFT_DELETE
    po = models.ForeignKey("procurement.ProcurementOrder", related_name='lines', on_delete=models.CASCADE, verbose_name=_('Satınalma Siparişi'))
    material = models.ForeignKey("core.Material", on_delete=models.PROTECT, null=False, blank=False, verbose_name=_('Malzeme'))
    uom = UOMField(null=False, blank=False)
    quantity = models.DecimalField(_('Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(Decimal('0.00'))])
    quantity_received = models.DecimalField(_('Alınan Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    unit_price = models.DecimalField(_('Birim Fiyat'), max_digits=32, decimal_places=2, null=True, blank=False, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(_('Vergi Oranı'), max_digits=4, decimal_places=3, null=True, blank=False, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    history = HistoricalRecords()
    
    def clean(self):
        integer_uoms = [
            UOMField.Unit.PIECE,
            UOMField.Unit.BOX,
            UOMField.Unit.PALLET
        ]
        errors = {}
        if self.uom in integer_uoms:
            if self.quantity is not None and self.quantity % 1 != 0:
                errors['quantity'] = 'Miktar tam sayı olmalıdır.'
            if self.quantity_received is not None and self.quantity_received % 1 != 0:
                errors['quantity_received'] = 'Miktar tam sayı olmalıdır.'
        
        # Validate quantity_received doesn't exceed quantity
        if self.quantity is not None and self.quantity_received is not None:
            if self.quantity_received > self.quantity:
                errors['quantity_received'] = _('Alınan miktar, sipariş edilen miktarı aşamaz.')
        
        if errors:
            raise ValidationError(errors)

    @property
    def quantity_left(self):
        """Returns the quantity that is still to be received."""
        return self.quantity - self.quantity_received

    @property
    def total_without_tax(self):
        if self.unit_price is None or self.quantity is None:
            return None
        return self.unit_price * self.quantity

    @property
    def total_with_tax(self):
        if self.unit_price is None or self.quantity is None or self.tax_rate is None:
            return None
        return (self.unit_price * self.quantity) * (1 + self.tax_rate)
        