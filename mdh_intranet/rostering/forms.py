from django import forms
from .models import Roster, ShiftSwapRequest
from django.contrib.auth.models import User

class RosterForm(forms.ModelForm):
    class Meta:
        model = Roster
        fields = ['department', 'start_date', 'end_date', 'is_published']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Emergency Room, ICU'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SwapRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftSwapRequest
        fields = ['requested_colleague', 'reason']
        widgets = {
            'requested_colleague': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please state why you need to swap...'}),
        }

    def __init__(self, *args, **kwargs):
        # Allow excluding the requesting user from the list
        requester = kwargs.pop('requester', None)
        super().__init__(*args, **kwargs)
        if requester:
            self.fields['requested_colleague'].queryset = User.objects.exclude(id=requester.id).order_by('first_name', 'last_name')
