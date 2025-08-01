from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete import SOFT_DELETE, SOFT_DELETE_CASCADE
from safedelete.models import SafeDeleteModel
from simple_history.models import HistoricalRecords
from core.fields import CurrencyField, UOMField
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class SalesOrder(SafeDeleteModel):
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
        ('billed', 'Faturalandı'),
        ('paid', 'Ödendi'),
        ('cancelled', 'İptal edildi')
    ]
    
    so_number = models.CharField(_("SO #no"), max_length=50, unique=True, null=True, blank=False)
    customer = models.ForeignKey("core.Company", on_delete=models.CASCADE, blank=False, null=True, verbose_name=_('Müşteri'))
    payment_term = models.CharField(_('Ödeme Koşulları'), max_length=20, choices=PAYMENT_TERMS)
    payment_method = models.CharField(_('Ödeme Yöntemi'), max_length=20, choices=PAYMENT_METHODS)
    incoterms = models.CharField(_('Teslim Şekli (Incoterms)'), max_length=20, choices=INCOTERMS)
    trade_discount = models.DecimalField(_('Ticari İskonto'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_in_days = models.DurationField(_('Vade Günü'))
    due_discount = models.DecimalField(_('Vade İskontosu'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_discount_days = models.DurationField(_('Vade İskonto Günü'), null=True, blank=False)
    invoice_date =  models.DateField(_('Fatura Tebliğ Tarihi'), null=True, blank=False)
    invoice_number = models.CharField(_("Fatura #no"), max_length=50, blank=False, null=True)
    description = models.TextField(_('Açıklama'), max_length=500)
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS, default="draft") 
    currency = CurrencyField(null=False, blank=False)
    delivery_address = models.CharField(_('Teslimat Adresi'), max_length=250, null=True, blank=False)
    dispatch_ordered = models.BooleanField(_('Sevk emri verildi'), null = False, blank=False, default = False)
    history = HistoricalRecords()
    
    class Meta:
        permissions = [
            ("submit_salesorder", "Sales officer approval"),
            ("approve_salesorder", "Customer approval registration"),
            ("dispatch_salesorder", "Sales order dispatching"),
            ("cancel_salesorder", "Sales order cancel permission"),
            ("bill_salesorder", "Can set invoice issuance date, also means invoice is approved"),
        ]

    def __str__(self):
        return str(self.so_number)
    
    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        
        if creating and not self.so_number:
            prefix = "SO-#"
            year = str(datetime.now().year)[-2:]
            pk_str = str(self.pk)
            zeros_len = 16 - (len(prefix) + len(year) + len(pk_str))
            zeros = '0' * max(0, zeros_len)
            self.so_number = f"{prefix}{year}{zeros}{pk_str}"[:16]
            super().save(update_fields=["so_number"])
            
    @property
    def total_price_without_tax(self):
        subtotal = sum(
            (line.unit_price * line.quantity)
            for line in self.lines.all() # type: ignore
            if line.unit_price is not None and line.quantity is not None
        )
        discount = subtotal * (self.trade_discount + self.due_discount)
        return subtotal - discount

    @property
    def total_price_with_tax(self):
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
        return all(line.quantity_left <= 0 for line in self.lines.all()) # type: ignore
    
    @property
    def invoice_accepted(self):
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

    # ---- STATE MANAGEMENT BELOW ----
    
    def set_dispatch_ordered(self, value=True):
        self.dispatch_ordered = value
        self.save(update_fields=["dispatch_ordered"])


    def can_transition_to(self, new_status, user=None):
        transitions = {
            'draft': ['submitted'],
            'submitted': ['approved', 'cancelled', 'draft'],
            'approved': ['billed', 'cancelled'],
            'billed': ['paid'],
            'paid': [],
            'cancelled': []
        }
        return new_status in transitions.get(self.status, [])

    def validate_status_requirements(self, new_status):
        errors = {}
        if new_status == 'submitted':
            if self.lines.count() <= 0: # type: ignore
                errors['lines'] = _('Satış siparişinde satır yok')
            missing_price_lines = [line for line in self.lines.all() if line.unit_price is None] # type: ignore
            if missing_price_lines:
                errors['lines'] = _('Satırların bir veya daha fazlasında birim fiyat eksik.')
            required_fields = ['payment_term', 'customer', 'payment_method', 'incoterms', 'description', 'currency', 'delivery_address']
            for field in required_fields:
                if not getattr(self, field, None):
                    errors[field] = _("'%(field)s' alanı gereklidir.") % {'field': field}
            if self.payment_term in ['NET_T', 'PARTIAL_ADVANCE']:
                if not getattr(self, 'due_in_days', None):
                    errors['due_in_days'] = _('Bu vade tipi için vade günü gereklidir.')

        elif new_status == 'billed':
            if not getattr(self, 'invoice_date', None):
                errors['invoice_date'] = _("Faturalandı durumunda 'invoice_date' alanı gereklidir.")
            if not getattr(self, 'invoice_number', None):
                errors['invoice_number'] = _("Faturalandı durumunda 'invoice_number' alanı gereklidir.")

        return errors

    def change_status(self, new_status, user=None, **kwargs):
        if not self.can_transition_to(new_status, user):
            current_display = dict(self.STATUS).get(self.status, self.status)
            new_display = dict(self.STATUS).get(new_status, new_status)
            raise ValidationError(_("%(current)s durumundan %(new)s durumuna geçiş yapılamaz") % {
                'current': current_display,
                'new': new_display
            })

        errors = self.validate_status_requirements(new_status)
        if errors:
            raise ValidationError(errors)

        if new_status == 'billed':
            if 'invoice_date' in kwargs:
                self.invoice_date = kwargs['invoice_date']
            if 'invoice_number' in kwargs:
                self.invoice_number = kwargs['invoice_number']

        self.status = new_status
        self.save()
        return self

    def get_allowed_transitions(self, user=None):
        transitions = {
            'draft': ['submitted'],
            'submitted': ['approved', 'cancelled', 'draft'],
            'approved': ['billed', 'cancelled'],
            'billed': ['paid'],
            'paid': [],
            'cancelled': []
        }
        return transitions.get(self.status, [])
    
    
class SalesOrderLine(SafeDeleteModel):
    
    _safedelete_policy = SOFT_DELETE
    so = models.ForeignKey("sales.SalesOrder", related_name='lines', verbose_name=_("Satış Emri"), on_delete=models.CASCADE)
    line_number = models.IntegerField(_("#"))
    material = models.ForeignKey("core.Material", on_delete=models.PROTECT, null=False, blank=False, verbose_name=_('Malzeme'))
    quantity = models.DecimalField(_('Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(Decimal('0.00'))])
    uom = UOMField(null=False, blank=False)
    quantity_sent = models.DecimalField(_('Sevk Edilen Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
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
            if self.quantity_sent is not None and self.quantity_sent % 1 != 0:
                errors['quantity_sent'] = 'Miktar tam sayı olmalıdır.'
        
        # Validate quantity_received doesn't exceed quantity
        if self.quantity is not None and self.quantity_sent is not None:
            if self.quantity_sent > self.quantity:
                errors['quantity_sent'] = _('Gönderilen miktar, sipariş edilen miktarı aşamaz.')
        
        if errors:
            raise ValidationError(errors)
            
    def save(self, *args, **kwargs):
        if not self.line_number:
            last_line = SalesOrderLine.objects.filter(so=self.so).aggregate(
                models.Max('line_number')
            )['line_number__max']
            self.line_number = (last_line or 0) + 1
        super().save(*args, **kwargs)

    @property
    def quantity_left(self):
        """Returns the quantity that is still to be sent."""
        return self.quantity - self.quantity_sent

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