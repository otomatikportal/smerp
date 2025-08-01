import requests
import logging
from decimal import Decimal
from datetime import date
from celery import shared_task
from finance.models import CurrencyExchangeRate

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_daily_exchange_rates(self):
    """
    Fetch daily exchange rates for specific currency pairs:
    TRY -> USD, EUR, RUB, GBP
    USD, EUR, RUB, GBP -> TRY
    
    Runs daily at 5:00 AM
    """
    today = date.today()
    
    try:
        logger.info(f"Starting exchange rate fetch for {today}")
        
        # Define the currency pairs we need
        currency_pairs = [
            # TRY as source
            ('TRY', 'USD'),
            ('TRY', 'EUR'), 
            ('TRY', 'RUB'),
            ('TRY', 'GBP'),
            # Other currencies to TRY
            ('USD', 'TRY'),
            ('EUR', 'TRY'),
            ('RUB', 'TRY'),
            ('GBP', 'TRY'),
        ]
        
        rates_created = 0
        
        # Process each currency pair
        for from_currency, to_currency in currency_pairs:
            try:
                rate = fetch_exchange_rate(from_currency, to_currency)
                if rate:
                    # Create or update the exchange rate
                    exchange_rate, created = CurrencyExchangeRate.objects.update_or_create(
                        date=today,
                        from_currency=from_currency,
                        to_currency=to_currency,
                        defaults={'rate': rate}
                    )
                    
                    if created:
                        rates_created += 1
                        logger.info(f"Created new rate: {from_currency}/{to_currency} = {rate}")
                    else:
                        logger.info(f"Updated existing rate: {from_currency}/{to_currency} = {rate}")
                else:
                    logger.warning(f"Could not fetch rate for {from_currency}/{to_currency}")
                    
            except Exception as e:
                logger.error(f"Error processing {from_currency}/{to_currency}: {e}")
                continue
        
        logger.info(f"Exchange rate fetch completed. Created {rates_created} new rates.")
        return f"Successfully processed {len(currency_pairs)} currency pairs. Created {rates_created} new rates."
        
    except Exception as exc:
        logger.error(f"Exchange rate fetch failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


def fetch_exchange_rate(from_currency, to_currency):
    """
    Fetch exchange rate from ExchangeRate-API for a specific currency pair.
    Uses the free API without key.
    """
    try:
        # Use the free API endpoint with the source currency as base
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        
        logger.info(f"Fetching rate from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data:
            logger.warning(f"No rates found in API response for {from_currency}")
            return None
            
        rates = data['rates']
        
        if to_currency not in rates:
            logger.warning(f"Target currency {to_currency} not found in rates for {from_currency}")
            return None
            
        rate_value = rates[to_currency]
        
        # Convert to Decimal for precision
        return Decimal(str(rate_value))
        
    except requests.RequestException as e:
        logger.error(f"Error fetching rate for {from_currency}/{to_currency}: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing rate for {from_currency}/{to_currency}: {e}")
        return None


@shared_task
def fetch_specific_exchange_rate(from_currency, to_currency, target_date=None):
    """
    Fetch a specific exchange rate pair for a given date.
    Can be used for manual updates or missing data.
    """
    if target_date is None:
        target_date = date.today()
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    
    try:
        rate = fetch_exchange_rate(from_currency, to_currency)
        if rate:
            exchange_rate, created = CurrencyExchangeRate.objects.update_or_create(
                date=target_date,
                from_currency=from_currency,
                to_currency=to_currency,
                defaults={'rate': rate}
            )
            
            action = "Created" if created else "Updated"
            logger.info(f"{action} rate: {from_currency}/{to_currency} = {rate} for {target_date}")
            
            return f"{action} exchange rate {from_currency}/{to_currency} = {rate}"
        else:
            return f"Failed to fetch rate for {from_currency}/{to_currency}"
            
    except Exception as e:
        logger.error(f"Error in fetch_specific_exchange_rate: {e}")
        return f"Error: {e}"
    
    
    

    
    
    



