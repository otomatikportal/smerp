from django.db import models
from django.forms import CharField
from simple_history.models import HistoricalRecords
from core.fields import CurrencyField, UOMField
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE, SOFT_DELETE_CASCADE
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
    
class MaterialDemand(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    STATUS = [
        ("submitted", "Gönderildi"),
        ("approved", "Onaylandı"),
        ("closed", "Kapandı"),
    ]
    
    demand_no = models.CharField(_('Talep No'), max_length=50, blank=True, null=True, unique=True)
    material = models.ForeignKey("core.Material", related_name='demands' ,on_delete=models.PROTECT, null=False, blank=False, verbose_name=_('Malzeme'))
    quantity = models.DecimalField(_('Miktar'), max_digits=12, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(0.00)])
    uom = UOMField()
    deadline = models.DateField(_('Son Tarih'), auto_now=False, auto_now_add=False)
    description = models.TextField(_('Açıklama'), max_length=500)
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS, default="draft")
    history = HistoricalRecords()

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
        ("NET_T", "Net T"),
        ("DUE_ON_RECEIPT", "Due on Receipt"),
        ("CIA", "Cash in Advance"),
        ("CWO", "Cash with Order"),
        ("COD", "Cash on Delivery"),
        ("CAD", "Cash Against Documents"),
        ("EOM", "End of Month"),
        ("T_EOM", "T Days End of Month"),
        ("PROX", "Proximo"),
        ("PARTIAL_ADVANCE", "Partial Payment in Advance"),
        ("LC", "Letter of Credit"),
        ("DC", "Documentary Collection"),
        ("X_Y_NET_T", "X/Y Net T"),
        ("TRADE_DISCOUNT", "Trade Discount"),
    ]
    
    INCOTERMS = [
        ("EXW", "Ex Works"),
        ("FCA", "Free Carrier"),
        ("FAS", "Free Alongside Ship"),
        ("FOB", "Free On Board"),
        ("CFR", "Cost and Freight"),
        ("CIF", "Cost, Insurance and Freight"),
        ("CPT", "Carriage Paid To"),
        ("CIP", "Carriage and Insurance Paid To"),
        ("DAP", "Delivered At Place"),
        ("DPU", "Delivered at Place Unloaded"),
        ("DDP", "Delivered Duty Paid"),
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
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi'),
        ('ordered', 'Sipariş verildi'),
        ('billed', 'Faturalandı'),
        ('paid', 'Ödendi'),
        ('cancelled', 'İptal edildi')
    ]
    
    vendor = models.ForeignKey("core.Company", on_delete=models.CASCADE, blank=False, null=True, verbose_name=_('Tedarikçi'))
    payment_term = models.CharField(_('Vade Şartı'), max_length=20, choices=PAYMENT_TERMS)
    payment_method = models.CharField(_('Ödeme Yöntemi'), max_length=20, choices=PAYMENT_METHODS)
    incoterms = models.CharField(_('Teslim Şekli (Incoterms)'), max_length=20, choices=INCOTERMS)
    trade_discount = models.DecimalField(_('Ticari İskonto'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_in_days = models.DurationField(_('Vade Günü'))
    due_discount = models.DecimalField(_('Vade İskontosu'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    due_discount_days = models.DurationField(_('Vade İskonto Günü'))
    invoice_accepted =  models.DateField(_('Fatura Kabul Tarihi'))
    description = models.TextField(_('Açıklama'), max_length=500)
    status = models.CharField(_('Durum'), max_length=20, choices=STATUS, default="draft") 
    currency = CurrencyField(null=False, blank=False)
    delivery_address = models.CharField(_('Teslimat Adresi'), max_length=250, null=True, blank=False)
    history = HistoricalRecords()
    
    @property
    def total_price_without_tax(self):
        # Sum of unit_price * quantity for all lines, minus trade_discount and due_discount
        subtotal = sum((line.unit_price * (line.quantity) for line in self.lines.all()), Decimal("0.00")) #type: ignore
        discount = subtotal * (self.trade_discount + self.due_discount)
        return subtotal - discount

    @property
    def total_price_with_tax(self):
        # Sum of (unit_price * quantity) * (1 + tax_rate) for all lines, minus discounts
        subtotal = sum((line.unit_price * (line.quantity) for line in self.lines.all()), Decimal("0.00")) #type: ignore
        discount = subtotal * (self.trade_discount + self.due_discount)
        subtotal_after_discount = subtotal - discount
        tax_total = sum((line.unit_price * (line.quantity) * (line.tax_rate) for line in self.lines.all()), Decimal("0.00")) #type: ignore
        return subtotal_after_discount + tax_total

    @property
    def all_received(self):
        """Returns True if all order lines have no missing quantity (quantity_left <= 0)."""
        return all(line.quantity_left <= 0 for line in self.lines.all()) #type: ignore
    
class ProcurementInvoice(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    invoice_number = models.CharField(_('Fatura No'), max_length=50, null=False, blank=False)
    po = models.ForeignKey("procurement.ProcurementOrder", related_name='invoices', on_delete=models.CASCADE, verbose_name=_('Satınalma Siparişi'))
    
class ProcurementOrderLine(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    po = models.ForeignKey("procurement.ProcurementOrder", related_name='lines', on_delete=models.CASCADE, verbose_name=_('Satınalma Siparişi'))
    material = models.ForeignKey("core.Material", on_delete=models.CASCADE, null=False, blank=False, verbose_name=_('Malzeme'))
    uom = UOMField(null=False, blank=False)
    quantity = models.DecimalField(_('Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(0.00)])
    quantity_received = models.DecimalField(_('Alınan Miktar'), max_digits=21, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(0.00)])
    unit_price = models.DecimalField(_('Birim Fiyat'), max_digits=32, decimal_places=2)
    tax_rate = models.DecimalField(_('Vergi Oranı'), max_digits=4, decimal_places=3, default=Decimal("0.000"), validators=[MinValueValidator(0), MaxValueValidator(1)])
    history = HistoricalRecords()

    @property
    def quantity_left(self):
        """Returns the quantity that is still to be received."""
        return self.quantity - self.quantity_received
    