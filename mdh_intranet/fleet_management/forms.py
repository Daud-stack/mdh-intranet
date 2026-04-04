from django import forms
from .models import Vehicle, TripLog, FuelLog

class TripLogForm(forms.ModelForm):
    class Meta:
        model = TripLog
        fields = ['vehicle', 'start_mileage', 'origin', 'destination', 'purpose']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'start_mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Odometer at start'}),
            'origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Hospital'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Clinic A / Patient Address'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for trip...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='AVAILABLE').order_by('license_plate')

class EndTripForm(forms.ModelForm):
    class Meta:
        model = TripLog
        fields = ['end_mileage', 'notes']
        widgets = {
            'end_mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Odometer at end'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Incidents, delays, etc.'}),
        }

class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['vehicle', 'date', 'liters', 'cost', 'odometer', 'receipt']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'liters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'odometer': forms.NumberInput(attrs={'class': 'form-control'}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }
