from django.db import models
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel
from safedelete.config import SOFT_DELETE
from django.apps import apps

    
class Material(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    MATERIAL_CATEGORIES = [
        ('supplied', 'Tedarik'), #TED-
        ('cardboard', 'Koli/Karton'), #KAR-
        ('part', 'Parça/Yarı-mamul'), #PAR-
        ('good', 'Satılabilir ürün'), #SAT-
        ('administrative', 'İdari malzeme'), #IDA-
        ('pallet', 'palet'), #PLT-
        ('undefined', 'Belirtilmemiş') #UND-
    ]
    name = models.CharField(_('Ad'), max_length=128, blank=False, null=True)
    category = models.CharField(_('Kategori'), max_length=32, choices=MATERIAL_CATEGORIES, blank=False, null=False, default='undefined')
    internal_code = models.CharField(_('İç Kod'), max_length=14, blank=True, null=True, unique=True)
    description = models.TextField(_('Açıklama'), max_length=500)
    history = HistoricalRecords()
    
    def __str__(self):
        return str(self.name)
    
    @property
    def latest_cost(self):
        """
        Returns the cost field of the latest VariableCost for this material.
        Safe for use in serializers and querysets.
        """
        VariableCost = apps.get_model('sales', 'VariableCost')
        latest = VariableCost.objects.filter(material=self).order_by('-id').first()
        return latest.cost if latest else None #type: ignore
    
    def latest_cost_for_uom(self, uom):
        """
        Returns the cost field of the latest VariableCost for this material with the specified UOM.
        Args:
            uom: The unit of measure to filter by
        Returns:
            Decimal cost if found, None otherwise
        """
        VariableCost = apps.get_model('sales', 'VariableCost')
        latest = VariableCost.objects.filter(material=self, uom=uom).order_by('-id').first()
        return latest.cost if latest else None #type: ignore

    PREFIX_MAP = {
        'supplied': 'TED-',
        'cardboard': 'KAR-',
        'part': 'PAR-',
        'good': 'SAT-',
        'administrative': 'IDA-',
        'pallet': 'PLT-',
        'undefined': 'UND-'
    }
    
    #UND-YY99999999
    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.internal_code:
            prefix = self.PREFIX_MAP.get(self.category, 'UND-')
            year = str(timezone.now().year)[-2:]
            pk_str = str(self.pk)
            # prefix (4) + year (2) + zeros (variable) + pk (variable) = 14
            zeros_len = 14 - (len(prefix) + len(year) + len(pk_str))
            zeros = '0' * max(0, zeros_len)
            self.internal_code = f"{prefix}{year}{zeros}{pk_str}"[:14]
            super().save(update_fields=["internal_code"])
            
    def generate_internal_code(self):
        """
        Generates and sets internal_code using PK.
        Should be called AFTER the instance is saved to DB (i.e., has a PK).
        """
        if not self.pk:
            raise ValueError("Cannot generate internal_code without a primary key (pk)")
        if self.internal_code:
            return  # Already has code

        prefix = self.PREFIX_MAP.get(self.category, 'UND-')
        year = str(timezone.now().year)[-2:]
        pk_str = str(self.pk)
        zeros_len = 14 - (len(prefix) + len(year) + len(pk_str))
        zeros = '0' * max(0, zeros_len)
        self.internal_code = f"{prefix}{year}{zeros}{pk_str}"[:14]