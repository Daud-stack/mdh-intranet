from django import forms
from .models import AuditSubmission

class AuditSubmissionForm(forms.ModelForm):
    class Meta:
        model = AuditSubmission
        fields = ['department_audited', 'notes']
        widgets = {
            'department_audited': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ICU, General Ward B'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any overall observations?'}),
        }
