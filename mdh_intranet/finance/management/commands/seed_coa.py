from django.core.management.base import BaseCommand
from mdh_intranet.finance.models import Account

class Command(BaseCommand):
    help = 'Seeds a default Chart of Accounts for the hospital'

    def handle(self, *args, **kwargs):
        accounts = [
            # ASSETS (1000s)
            {'code': '1000', 'name': 'Main Bank Account (USD)', 'type': 'ASSET'},
            {'code': '1010', 'name': 'Petty Cash', 'type': 'ASSET'},
            {'code': '1100', 'name': 'Accounts Receivable', 'type': 'ASSET'},
            {'code': '1200', 'name': 'Medical Supplies Inventory', 'type': 'ASSET'},
            
            # LIABILITIES (2000s)
            {'code': '2000', 'name': 'Accounts Payable', 'type': 'LIABILITY'},
            {'code': '2100', 'name': 'Salaries Payable', 'type': 'LIABILITY'},
            
            # EQUITY (3000s)
            {'code': '3000', 'name': 'Owner Equity', 'type': 'EQUITY'},
            {'code': '3100', 'name': 'Retained Earnings', 'type': 'EQUITY'},
            
            # REVENUE (4000s)
            {'code': '4000', 'name': 'Patient Consultation Revenue', 'type': 'REVENUE'},
            {'code': '4100', 'name': 'Laboratory Service Revenue', 'type': 'REVENUE'},
            {'code': '4200', 'name': 'Pharmacy Sales Revenue', 'type': 'REVENUE'},
            
            # EXPENSES (5000s)
            {'code': '5000', 'name': 'Staff Salaries', 'type': 'EXPENSE'},
            {'code': '5100', 'name': 'Rent & Utilities', 'type': 'EXPENSE'},
            {'code': '5200', 'name': 'Medical Consumables', 'type': 'EXPENSE'},
            {'code': '5300', 'name': 'Vehicle Maintenance & Fuel', 'type': 'EXPENSE'},
        ]

        created_count = 0
        for acc_data in accounts:
            obj, created = Account.objects.get_or_create(
                code=acc_data['code'],
                defaults={
                    'name': acc_data['name'],
                    'type': acc_data['type']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} accounts.'))
