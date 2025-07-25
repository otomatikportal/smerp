from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from simple_history.models import HistoricalRecords
from core.fields import UOMField


class VariableCost(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    material = models.ForeignKey("core.Material", verbose_name=_("Malzeme"), on_delete=models.CASCADE, blank=False, null=False)
    cost = models.DecimalField(_("Birim maliyeti"), max_digits=30, decimal_places=3, blank=False, null=False)
    uom = UOMField(blank=False, null=False)
    history = HistoricalRecords()
    