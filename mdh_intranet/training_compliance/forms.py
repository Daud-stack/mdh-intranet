from django import forms
from .models import Certification

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['course', 'date_completed', 'certificate_file', 'notes']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'date_completed': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes about the training'}),
        }
