from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]
    
    code = models.CharField(max_length=20, unique=True, verbose_name="Account Code")
    name = models.CharField(max_length=100, verbose_name="Account Name")
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Helpful for reports
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def current_balance(self):
        """Calculates the current balance for this account."""
        # This will be more efficient with aggregation in production
        items = self.journal_items.all()
        debits = sum(item.debit for item in items)
        credits = sum(item.credit for item in items)
        
        # Debits increase Assets and Expenses
        if self.type in ['ASSET', 'EXPENSE']:
            return debits - credits
        else:
            return credits - debits

class JournalEntry(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, help_text="Invoice #, Receipt #, etc.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Journal Entries"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Entry {self.id} - {self.date}"

    def is_balanced(self):
        """Checks if total debits equal total credits."""
        items = self.items.all()
        if not items.exists():
            return False
        total_debit = sum(item.debit for item in items)
        total_credit = sum(item.credit for item in items)
        return total_debit == total_credit

class JournalItem(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_items')
    
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Currency Support
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('ZiG', 'ZiG')], default='USD')
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1.0)
    
    # Amount in Base Currency (USD) for unified reporting
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        # Calculate base amount (assuming USD is base)
        if self.currency == 'USD':
            self.base_amount = self.debit - self.credit
        else:
            # If ZiG, convert to USD using rate
            self.base_amount = (self.debit - self.credit) / self.exchange_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account.name} - {'Dr' if self.debit else 'Cr'}"

class ExchangeRate(models.Model):
    date = models.DateField(default=timezone.now)
    base_currency = models.CharField(max_length=3, default='USD')
    target_currency = models.CharField(max_length=3, default='ZiG')
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date', 'base_currency', 'target_currency']

    def __str__(self):
        return f"{self.date}: 1 {self.base_currency} = {self.rate} {self.target_currency}"

class ImportTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Store mapping as JSON: {"column_name": "target_field"}
    mapping_config = models.JSONField()
    
    # Default accounts for one-sided imports (e.g. Bank Statement)
    default_debit_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    default_credit_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ImportLog(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    template = models.ForeignKey(ImportTemplate, on_delete=models.SET_NULL, null=True)
    
    rows_processed = models.IntegerField(default=0)
    rows_successful = models.IntegerField(default=0)
    rows_failed = models.IntegerField(default=0)
    
    log_details = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Import {self.id} - {self.filename}"
