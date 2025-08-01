from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from core.fields import CurrencyField
from django.core.validators import MinValueValidator
from decimal import Decimal

class AccountMovement(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    
    MOVEMENT_TYPES = [
        ('debit', _('Borç')),
        ('credit', _('Alacak')),
    ]
    
    # Core fields
    account = models.ForeignKey('Account', on_delete=models.PROTECT, related_name='movements', verbose_name=_('Hesap'))
    movement_type = models.CharField(_('Hareket Türü'), max_length=10, choices=MOVEMENT_TYPES, null=False, blank=False)
    amount = models.DecimalField(_('Tutar'), max_digits=15, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(Decimal('0.00'))])
    currency = CurrencyField()
    description = models.TextField(_('Açıklama'), max_length=500, null=False, blank=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Hesap Hareketi')
        verbose_name_plural = _('Hesap Hareketleri')
        ordering = ['-id']
        
    def __str__(self):
        return f"{self.account.account_name} - {self.amount} TL"