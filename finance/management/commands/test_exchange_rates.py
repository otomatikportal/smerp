from django.core.management.base import BaseCommand
from finance.tasks import fetch_specific_exchange_rate
from finance.tasks import fetch_exchange_rate
from finance.models import CurrencyExchangeRate
from datetime import date
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test exchange rate fetching functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-single',
            action='store_true',
            help='Test fetching a single currency pair',
        )
        parser.add_argument(
            '--from-currency',
            type=str,
            default='TRY',
            help='Source currency (default: TRY)',
        )
        parser.add_argument(
            '--to-currency', 
            type=str,
            default='USD',
            help='Target currency (default: USD)',
        )

    def handle(self, *args, **options):
        if options['test_single']:
            # Test single currency pair
            from_curr = options['from_currency']
            to_curr = options['to_currency']
            
            self.stdout.write(f'Testing single exchange rate: {from_curr} -> {to_curr}')
            
            # Test the actual API call
            rate = fetch_exchange_rate(from_curr, to_curr)
            if rate:
                self.stdout.write(self.style.SUCCESS(f'Fetched rate: {from_curr}/{to_curr} = {rate}'))
                
                # Save to database
                today = date.today()
                exchange_rate, created = CurrencyExchangeRate.objects.update_or_create(
                    date=today,
                    from_currency=from_curr,
                    to_currency=to_curr,
                    defaults={'rate': rate}
                )
                action = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f'{action} database record'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch rate for {from_curr}/{to_curr}'))
            
        else:
            # Test all currency pairs
            self.stdout.write('Testing all exchange rate pairs...')
            
            currency_pairs = [
                ('TRY', 'USD'), ('TRY', 'EUR'), ('TRY', 'RUB'), ('TRY', 'GBP'),
                ('USD', 'TRY'), ('EUR', 'TRY'), ('RUB', 'TRY'), ('GBP', 'TRY'),
            ]
            
            today = date.today()
            success_count = 0
            
            for from_curr, to_curr in currency_pairs:
                self.stdout.write(f'Fetching {from_curr} -> {to_curr}...')
                
                rate = fetch_exchange_rate(from_curr, to_curr)
                if rate:
                    exchange_rate, created = CurrencyExchangeRate.objects.update_or_create(
                        date=today,
                        from_currency=from_curr,
                        to_currency=to_curr,
                        defaults={'rate': rate}
                    )
                    success_count += 1
                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f'  {action}: {rate}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  Failed to fetch'))
            
            self.stdout.write(self.style.SUCCESS(f'Completed! {success_count}/{len(currency_pairs)} successful'))
            
        self.stdout.write(self.style.SUCCESS('Test completed!'))
