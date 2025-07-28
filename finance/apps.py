from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'
    
    def ready(self):
        from django.db.models.signals import post_migrate
        
        def create_initial_accounts(sender, **kwargs):
            from django.db import transaction
            from .models import Account
            
            # Create initial accounts if they don't exist
            try:
                with transaction.atomic():
                    # Main account groups based on Turkish Uniform Chart of Accounts
                    initial_accounts = [
                        # 10 - Hazır Değerler (Cash and Cash Equivalents - parent account)
                        {
                            'account_code': '10',
                            'account_name': 'Hazır Değerler',
                            'account_type': 'asset',
                            'account_category': 'current_assets',
                            'parent_account': None,
                            'description': ''
                        },
                        # 12 - Ticari Alacaklar (Accounts Receivable - parent account)
                        {
                            'account_code': '12',
                            'account_name': 'Ticari Alacaklar',
                            'account_type': 'asset',
                            'account_category': 'accounts_receivable',
                            'parent_account': None,
                            'description': ''
                        },
                        # 15 - Stoklar (Inventory - parent account)
                        {
                            'account_code': '15',
                            'account_name': 'Stoklar',
                            'account_type': 'asset',
                            'account_category': 'inventory',
                            'parent_account': None,
                            'description': ''
                        },
                        # 32 - Ticari Borçlar (Accounts Payable - parent account)
                        {
                            'account_code': '32',
                            'account_name': 'Ticari Borçlar',
                            'account_type': 'liability',
                            'account_category': 'accounts_payable',
                            'parent_account': None,
                            'description': ''
                        },
                        # 60 - Brüt Satışlar (Revenue - parent account)
                        {
                            'account_code': '60',
                            'account_name': 'Brüt Satışlar',
                            'account_type': 'revenue',
                            'account_category': 'revenue',
                            'parent_account': None,
                            'description': ''
                        },
                        # 62 - Satışların Maliyeti (Cost of Goods Sold - parent account)
                        {
                            'account_code': '62',
                            'account_name': 'Satışların Maliyeti',
                            'account_type': 'expense',
                            'account_category': 'cogs',
                            'parent_account': None,
                            'description': ''
                        },
                    ]
                    
                    for account_data in initial_accounts:
                        if not Account.objects.filter(account_code=account_data['account_code']).exists():
                            Account.objects.create(**account_data)
                            
            except Exception:
                # Ignore errors during app initialization (e.g., during migrations)
                pass
        
        post_migrate.connect(create_initial_accounts, sender=self)
