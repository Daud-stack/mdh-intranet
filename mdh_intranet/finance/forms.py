from django import forms
from django.forms import inlineformset_factory
from .models import JournalEntry, JournalItem, Account

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'description', 'reference']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill'}),
            'description': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'Transaction description...'}),
            'reference': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'REF-001...'}),
        }

class JournalItemForm(forms.ModelForm):
    class Meta:
        model = JournalItem
        fields = ['account', 'description', 'debit', 'credit', 'currency', 'exchange_rate']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'description': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'Line memo...'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control rounded-pill', 'step': '0.01'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control rounded-pill', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control rounded-pill', 'step': '0.000001'}),
        }

JournalItemFormSet = inlineformset_factory(
    JournalEntry, JournalItem, form=JournalItemForm,
    extra=2, can_delete=True
)

class FinancialImportForm(forms.Form):
    file = forms.FileField(label="Select File (CSV or Excel)", widget=forms.FileInput(attrs={'class': 'form-control rounded-pill'}))
    template = forms.ModelChoiceField(
        queryset=Account.objects.none(), # Will be ImportTemplate.objects.all() but let's be careful
        required=False,
        empty_label="-- New Template / Manual Mapping --",
        widget=forms.Select(attrs={'class': 'form-select rounded-pill'})
    )
    default_account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=True,
        label="Counter Account (e.g. Bank)",
        widget=forms.Select(attrs={'class': 'form-select rounded-pill'})
    )

    def __init__(self, *args, **kwargs):
        from .models import ImportTemplate
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = ImportTemplate.objects.all()
