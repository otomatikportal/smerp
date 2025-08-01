from django.db import models
from django.utils.translation import gettext_lazy as _

class GenderField(models.CharField):
    class Gender(models.TextChoices):
        MALE   = "e", _("Erkek")
        FEMALE = "k", _("Kadın")
        OTHER  = "b", _("Belirtilmedi")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 1)
        kwargs.setdefault("choices", self.Gender.choices)
        kwargs.setdefault("default",  self.Gender.OTHER)
        kwargs.setdefault("verbose_name", _("Cinsiyet"))
        super().__init__(*args, **kwargs)
        
        
class CurrencyField(models.CharField):
    class Currency(models.TextChoices):
        TRY = "TRY", _("Türk Lirası")
        USD = "USD", _("ABD Doları")
        EUR = "EUR", _("Euro")
        GBP = "GBP", _("İngiliz Sterlini")
        RUB = "RUB", _("Rus Rublesi")


    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 6)
        kwargs.setdefault("choices", self.Currency.choices)
        kwargs.setdefault("default",  self.Currency.TRY)
        super().__init__(*args, **kwargs)
        
class UOMField(models.CharField):
    class Unit(models.TextChoices):
        PIECE     = "ADT", _("Adet")
        KILOGRAM     = "KG",  _("Kilogram")
        GRAM         = "G",   _("Gram")
        LITER        = "L",   _("Litre")
        MILLILITER   = "ML",  _("Mililitre")
        METER        = "M",   _("Metre")
        BOX          = "BOX", _("Koli")
        PALLET       = "PLT", _("Palet")


    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 4)
        kwargs.setdefault("choices",    self.Unit.choices)
        kwargs.setdefault("default",    self.Unit.PIECE)
        kwargs.setdefault("verbose_name", _("Birim"))
        super().__init__(*args, **kwargs)