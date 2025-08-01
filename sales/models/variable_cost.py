from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from simple_history.models import HistoricalRecords
from core.fields import CurrencyField, UOMField
from django.conf import settings


# 3 Things can create cost, 
# ProcurementOrderLine objects after order status, 
# User, 
# Adding or Updating Boms

class VariableCost(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    # Explicit foreign keys for the three sources
    procurement_order = models.ForeignKey("procurement.ProcurementOrder",on_delete=models.CASCADE,blank=True,null=True,verbose_name=_("Satınalma Siparişi"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL, blank=True, null=True,verbose_name=_("Kullanıcı"))
    bom = models.ForeignKey(
        "bom.Bom",
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        verbose_name=_("Malzeme Listesi")
    )
    
    # Core cost fields
    material = models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.CASCADE)
    cost = models.DecimalField(_("Birim maliyeti"), max_digits=30, decimal_places=3)
    currency = CurrencyField(null=False, blank=False)
    uom = UOMField()
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _("Değişken Maliyet")
        verbose_name_plural = _("Değişken Maliyetler")
        indexes = [
            models.Index(fields=['material']),
            models.Index(fields=['procurement_order'], name='varcost_proc_order_idx'),
            models.Index(fields=['user'], name='varcost_user_idx'),
            models.Index(fields=['bom'], name='varcost_bom_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    models.Q(procurement_order__isnull=False, user__isnull=True, bom__isnull=True) |
                    models.Q(procurement_order__isnull=True, user__isnull=False, bom__isnull=True) |
                    models.Q(procurement_order__isnull=True, user__isnull=True, bom__isnull=False)
                ),
                name='one_source_only'
            )
        ]
    
    @property
    def source_type(self):
        """Property to get source type based on which foreign key is set"""
        if self.procurement_order:
            return 'Satın alma'
        elif self.user:
            return 'Kullanıcı'
        elif self.bom:
            return 'Reçete'
        return None
    
    @property
    def source_object(self):
        """Property to get the actual source object"""
        if self.procurement_order:
            return self.procurement_order
        elif self.user:
            return self.user
        elif self.bom:
            return self.bom
        return None
    
    @classmethod
    def get_by_source(cls, source_object):
        """Get VariableCost instances by source object"""
        from django.contrib.auth.models import User
        from procurement.models import ProcurementOrder
        from bom.models import Bom
        
        if isinstance(source_object, ProcurementOrder):
            return cls.objects.filter(procurement_order=source_object)
        elif isinstance(source_object, User):
            return cls.objects.filter(user=source_object)
        elif isinstance(source_object, Bom):
            return cls.objects.filter(bom=source_object)
        return cls.objects.none()