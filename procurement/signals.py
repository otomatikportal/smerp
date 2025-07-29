from django.db.models.signals import post_save
from django.dispatch import receiver
from procurement.models import ProcurementOrder
from sales.models import VariableCost
from finance.models import CurrencyExchangeRate
from datetime import date
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProcurementOrder)
def create_cost_data(sender, instance, **kwargs):
    if instance.status == 'approved':
        for line in instance.lines.all():
            if not VariableCost.objects.filter(
                procurement_order=instance,
                material=line.material
            ).exists():

                original_cost = line.unit_price
                original_currency = instance.currency

                if original_currency != 'TRY':
                    today = date.today()
                    try_cost = CurrencyExchangeRate.convert_amount(
                        amount=original_cost,
                        from_currency=original_currency,
                        to_currency='TRY',
                        target_date=today
                    )

                    if try_cost is not None:
                        final_cost = try_cost
                        final_currency = 'TRY'
                        rate_used = CurrencyExchangeRate.get_rate(
                            original_currency, 'TRY', today)
                        logger.info(
                            f"Converted cost: {original_cost} {original_currency} → {final_cost} TRY using rate {rate_used} for {today}")

                    else:
                        logger.warning(
                            f"No exchange rate found for {original_currency} to TRY on {today}. Searching for latest available rate...")

                        try_cost_latest = CurrencyExchangeRate.convert_amount(
                            amount=original_cost,
                            from_currency=original_currency,
                            to_currency='TRY',
                            target_date=today
                        )

                        if try_cost_latest is not None:
                            final_cost = try_cost_latest
                            final_currency = 'TRY'

                            latest_rate_obj = CurrencyExchangeRate.objects.filter(
                                from_currency=original_currency,
                                to_currency='TRY'
                            ).order_by('-date').first()

                            if latest_rate_obj:
                                rate_date = latest_rate_obj.date
                                rate_value = latest_rate_obj.rate
                                logger.warning(
                                    f"AUDIT: Used latest available rate from {rate_date} (rate: {rate_value}) to convert {original_cost} {original_currency} → {final_cost} TRY. Current date: {today}")
                            else:
                                logger.warning(
                                    f"AUDIT: Converted using latest rate {original_cost} {original_currency} → {final_cost} TRY, but could not determine rate date")
                        else:
                            final_cost = original_cost
                            final_currency = original_currency
                            logger.error(
                                f"AUDIT: NO EXCHANGE RATES AVAILABLE for {original_currency} to TRY. Using original cost: {original_cost} {original_currency}. This may cause inconsistent costing!")
                else:
                    final_cost = original_cost
                    final_currency = 'TRY'
                    logger.info(f"Cost already in TRY: {final_cost}")

                VariableCost.objects.create(
                    procurement_order=instance,
                    material=line.material,
                    cost=final_cost,
                    currency=final_currency,
                    uom=line.uom
                )