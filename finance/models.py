from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from core.fields import CurrencyField
from django.core.validators import MinValueValidator
from decimal import Decimal

class Account(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    
    ACCOUNT_TYPES = [
        ('asset', _('Varlık')),
        ('liability', _('Yükümlülük')),
        ('equity', _('Özkaynak')),
        ('revenue', _('Gelir')),
        ('expense', _('Gider')),
    ]
    
    ACCOUNT_CATEGORIES = [
        ('current_assets', _('Dönen Varlıklar')),
        ('accounts_receivable', _('Alacaklar')),
        ('inventory', _('Stok')),
        ('accounts_payable', _('Borçlar')),
        ('revenue', _('Satış Gelirleri')),
        ('cogs', _('Satışların Maliyeti')),
    ]
    
    # Core fields
    account_code = models.CharField(_('Hesap Kodu'), max_length=20, unique=True, null=False, blank=False)
    account_name = models.CharField(_('Hesap Adı'), max_length=128, null=False, blank=False)
    account_type = models.CharField(_('Hesap Türü'), max_length=20, choices=ACCOUNT_TYPES, null=False, blank=False)
    account_category = models.CharField(_('Hesap Kategorisi'), max_length=20, choices=ACCOUNT_CATEGORIES, null=False, blank=False)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts', verbose_name=_('Üst Hesap'))
    is_active = models.BooleanField(_('Aktif'), default=True)
    description = models.TextField(_('Açıklama'), max_length=500, blank=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Hesap')
        verbose_name_plural = _('Hesaplar')
        ordering = ['account_code']
        indexes = [
            models.Index(fields=['account_code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        super().clean()

        if self.parent_account:
            # Check if trying to set self as parent
            if self.parent_account == self:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'parent_account': _('Bir hesap kendisinin üst hesabı olamaz.')
                })
            
            current_parent = self.parent_account
            visited_accounts = {self.pk} if self.pk else set()
            
            while current_parent:
                if current_parent.pk in visited_accounts:
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'parent_account': _('Dairesel referans oluşturmak mümkün değildir. Seçilen üst hesap bu hesabın alt hesabıdır.')
                    })
                
                visited_accounts.add(current_parent.pk)
                current_parent = current_parent.parent_account
    
    def __str__(self):
        return f"{self.account_code}"
    
    
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
    description = models.TextField(_('Açıklama'), max_length=500, null=False, blank=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Hesap Hareketi')
        verbose_name_plural = _('Hesap Hareketleri')
        ordering = ['-id']
        
    def __str__(self):
        return f"{self.account.account_name} - {self.amount} TL"