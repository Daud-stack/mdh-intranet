from django import forms
from django.contrib.auth.models import User
from .models import ApprovalWorkflow, ApprovalStep

class ApprovalWorkflowForm(forms.ModelForm):
    class Meta:
        model = ApprovalWorkflow
        fields = ['module', 'object_repr', 'notes']
        widgets = {
            'module': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SOP, CAPA, Incident'}),
            'object_repr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of approval'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional submission notes'}),
        }

class ApprovalStepForm(forms.Form):
    approver = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(attrs={'class': 'form-select select2-user-picker'}),
        label="Select Approver"
    )
    role_label = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Department Head, Quality Manager'}),
        label="Role Title"
    )
