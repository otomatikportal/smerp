from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from core.fields import GenderField
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE


class Company(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    name = models.CharField(_('Ad'), max_length=50, blank=False, null=True)
    legal_name = models.CharField(_('Ticari Unvan'), max_length=128, blank=False, null=True, unique=True)
    e_mail = models.CharField(_('E-posta'), max_length=254, blank=False, null=True)
    website = models.CharField(_('Web Sitesi'), max_length=254, blank=False, null=True)
    phone = models.CharField(_('Telefon'), max_length=12, blank=False, null=True)
    description = models.TextField(_('Açıklama'), max_length=500)
    history = HistoricalRecords()
    
    def __str__(self):
        return str(self.name)
    
class Contact(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    ROLE_CHOICES = [
        ('owner', 'Firma sahibi'),
        ('employee', 'Çalışan'),
        ('salesperson', 'Satış temsilcisi'),
        ('procurement', 'Satın almacı')
    ]    
    
    company = models.ForeignKey("core.Company", related_name='contacts', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('Firma'))
    name = models.CharField(_('Ad'), max_length=128, blank=False, null=True)
    gender = GenderField()
    last_name = models.CharField(_('Soyad'), max_length=128, blank=False, null=True)
    role = models.CharField(_('Rol'), max_length=32, choices=ROLE_CHOICES, blank=False, null=True)
    e_mail = models.CharField(_('E-posta'), max_length=254, blank=False, null=True)
    phone = models.CharField(_('Telefon'), max_length=12, blank=False, null=True)
    description = models.TextField(_('Açıklama'), max_length=500)
    history = HistoricalRecords()