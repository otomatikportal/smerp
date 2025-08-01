from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from core.fields import CurrencyField
from django.core.validators import MinValueValidator
from decimal import Decimal

class CurrencyExchangeRate(models.Model):
    
    # Core fields
    date = models.DateField(_('Tarih'), null=False, blank=False)
    from_currency = CurrencyField(verbose_name=_('Kaynak Para Birimi'), null=False, blank=False)
    to_currency = CurrencyField(verbose_name=_('Hedef Para Birimi'), null=False, blank=False)
    rate = models.DecimalField(_('Kur'), max_digits=15, decimal_places=6, null=False, blank=False, validators=[MinValueValidator(Decimal('0.000001'))])
    
    class Meta:
        verbose_name = _('Döviz Kuru')
        verbose_name_plural = _('Döviz Kurları')
        ordering = ['-date', 'from_currency', 'to_currency']
        unique_together = ['date', 'from_currency', 'to_currency']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['from_currency', 'to_currency']),
            models.Index(fields=['date', 'from_currency', 'to_currency']),
        ]
    
    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        
        if self.from_currency == self.to_currency:
            raise ValidationError({
                'to_currency': _('Kaynak ve hedef para birimi aynı olamaz.')
            })
    
    def __str__(self):
        return f"{self.date} - {self.from_currency}/{self.to_currency}: {self.rate}"
    
    @classmethod
    def get_rate(cls, from_currency, to_currency, target_date=None):
        """
        Get exchange rate for a specific currency pair and date.
        If target_date is None, uses the latest available rate.
        """
        if target_date is None:
            # Get the latest date available
            latest_date = cls.objects.aggregate(models.Max('date'))['date__max']
            if not latest_date:
                return None
            target_date = latest_date
            
        try:
            rate_obj = cls.objects.filter(
                from_currency=from_currency,
                to_currency=to_currency,
                date=target_date
            ).first()
            
            return rate_obj.rate if rate_obj else None
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency, target_date=None):
        """
        Convert an amount from one currency to another using the exchange rate.
        """
        if from_currency == to_currency:
            return amount
            
        rate = cls.get_rate(from_currency, to_currency, target_date)
        if rate is None:
            return None
            
        return amount * rate