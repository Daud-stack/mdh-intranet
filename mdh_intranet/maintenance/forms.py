from django import forms
from .models import Asset, WorkOrder, MaintenanceTask, AssetReading

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['title', 'asset', 'order_type', 'priority', 'description', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What needs to be done?'}),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class AssetReadingForm(forms.ModelForm):
    class Meta:
        model = AssetReading
        fields = ['reading_type', 'value', 'unit']
        widgets = {
            'reading_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Temperature'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. °C'}),
        }

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'name', 'asset_id', 'serial_number', 'category', 'location', 'status', 
            'criticality', 'purchase_date', 'warranty_expiry', 'next_ppm_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_id': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'criticality': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_ppm_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
