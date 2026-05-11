from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Account, JournalEntry, JournalItem, ExchangeRate
from .forms import JournalEntryForm, JournalItemFormSet

@login_required
def dashboard(request):
    """Finance Dashboard with P&L and Cash Overview"""
    # 1. Cash Balance (Bank accounts start with 10)
    bank_accounts = Account.objects.filter(code__startswith='10', type='ASSET')
    total_cash = sum(acc.current_balance for acc in bank_accounts)
    
    # 2. P&L Summary (Current Month)
    start_of_month = timezone.now().replace(day=1)
    revenue = JournalItem.objects.filter(
        account__type='REVENUE', 
        entry__status='POSTED',
        entry__date__gte=start_of_month
    ).aggregate(total=Sum('base_amount'))['total'] or 0
    
    expenses = JournalItem.objects.filter(
        account__type='EXPENSE', 
        entry__status='POSTED',
        entry__date__gte=start_of_month
    ).aggregate(total=Sum('base_amount'))['total'] or 0
    
    # Revenue is credit-based, so it will be negative in base_amount (debit - credit)
    # We want absolute values for display
    net_profit = abs(revenue) - abs(expenses)
    
    # 3. Recent Transactions
    recent_entries = JournalEntry.objects.all().order_by('-date', '-created_at')[:10]
    
    context = {
        'total_cash': total_cash,
        'revenue': abs(revenue),
        'expenses': abs(expenses),
        'net_profit': net_profit,
        'recent_entries': recent_entries,
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def journal_list(request):
    """List all journal entries"""
    entries = JournalEntry.objects.all().select_related('created_by')
    return render(request, 'finance/journal_list.html', {'entries': entries})

@login_required
def journal_create(request):
    """Create a new Journal Entry with line items"""
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        formset = JournalItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            formset.instance = entry
            formset.save()
            
            # Auto-post for now if balanced
            if entry.is_balanced():
                entry.status = 'POSTED'
                entry.save()
            
            return redirect('finance:journal_list')
    else:
        form = JournalEntryForm()
        formset = JournalItemFormSet()
    
    return render(request, 'finance/journal_form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Journal Entry'
    })

@login_required
def ledger_view(request, account_id):
    """General Ledger for a specific account"""
    account = get_object_or_404(Account, pk=account_id)
    items = JournalItem.objects.filter(account=account, entry__status='POSTED').order_by('entry__date')
    
    # Calculate running balance
    balance = 0
    history = []
    for item in items:
        if account.type in ['ASSET', 'EXPENSE']:
            balance += (item.debit - item.credit)
        else:
            balance += (item.credit - item.debit)
        history.append({'item': item, 'balance': balance})
        
    return render(request, 'finance/ledger.html', {
        'account': account,
        'history': history,
        'final_balance': balance
    })

@login_required
def profit_loss(request):
    """Profit and Loss Report"""
    # Group by account type
    revenue_accounts = Account.objects.filter(type='REVENUE')
    expense_accounts = Account.objects.filter(type='EXPENSE')
    
    # Calculate totals
    rev_data = []
    total_rev = 0
    for acc in revenue_accounts:
        bal = acc.current_balance
        if bal != 0:
            rev_data.append({'account': acc, 'balance': bal})
            total_rev += bal
            
    exp_data = []
    total_exp = 0
    for acc in expense_accounts:
        bal = acc.current_balance
        if bal != 0:
            exp_data.append({'account': acc, 'balance': bal})
            total_exp += bal
            
    context = {
        'rev_data': rev_data,
        'total_rev': total_rev,
        'exp_data': exp_data,
        'total_exp': total_exp,
        'net_income': total_rev - total_exp,
        'period': 'Current Year'
    }
    return render(request, 'finance/profit_loss.html', context)


import pandas as pd
from .forms import FinancialImportForm
from .models import ImportTemplate, ImportLog

@login_required
def import_wizard(request):
    """
    Step-by-step import of financial data.
    """
    if request.method == 'POST' and 'upload' in request.POST:
        form = FinancialImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            default_account = form.cleaned_data['default_account']
            
            # Read file using pandas
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Store data in session for mapping step
                request.session['import_data'] = df.to_json()
                request.session['import_filename'] = file.name
                request.session['default_account_id'] = default_account.id
                
                context = {
                    'columns': df.columns.tolist(),
                    'preview': df.head(5).to_html(classes='table table-sm small'),
                    'accounts': Account.objects.all(),
                }
                return render(request, 'finance/import_mapping.html', context)
                
            except Exception as e:
                messages.error(request, f"Error reading file: {str(e)}")
    
    elif request.method == 'POST' and 'map' in request.POST:
        # Final processing
        try:
            data_json = request.session.get('import_data')
            df = pd.read_json(data_json)
            
            date_col = request.POST.get('date_col')
            desc_col = request.POST.get('desc_col')
            amount_col = request.POST.get('amount_col')
            default_acc_id = request.session.get('default_account_id')
            default_acc = Account.objects.get(pk=default_acc_id)
            
            # We also need a "category" account for the other side of the entry
            category_acc_id = request.POST.get('category_account')
            category_acc = Account.objects.get(pk=category_acc_id)
            
            success_count = 0
            for index, row in df.iterrows():
                try:
                    # Create Journal Entry
                    entry = JournalEntry.objects.create(
                        date=pd.to_datetime(row[date_col]).date(),
                        description=str(row[desc_col]),
                        status='POSTED',
                        created_by=request.user
                    )
                    
                    # Convert to decimal, handling potential NaN or strings
                    val = row[amount_col]
                    if pd.isna(val): continue
                    amount = Decimal(str(val))
                    
                    # Line 1: The Account chosen (e.g. Expense)
                    JournalItem.objects.create(
                        entry=entry,
                        account=category_acc,
                        debit=amount if amount > 0 else 0,
                        credit=abs(amount) if amount < 0 else 0,
                    )
                    
                    # Line 2: The contra line (The Bank/Cash)
                    JournalItem.objects.create(
                        entry=entry,
                        account=default_acc,
                        debit=abs(amount) if amount < 0 else 0,
                        credit=amount if amount > 0 else 0,
                    )
                    success_count += 1
                except Exception:
                    continue
            
            messages.success(request, f"Successfully imported {success_count} transactions.")
            return redirect('finance:dashboard')
            
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")

    form = FinancialImportForm()
    return render(request, 'finance/import_upload.html', {'form': form})
