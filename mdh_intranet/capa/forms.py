from django import forms
from .models import CAPARecord, CAPAComment


class CAPACreateForm(forms.ModelForm):
    """Form for creating a new CAPA record."""
    class Meta:
        model = CAPARecord
        fields = [
            'title', 'capa_type', 'source', 'priority',
            'linked_incident', 'description', 'impact_assessment',
            'assigned_to', 'target_completion_date', 'attachment',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title describing the non-conformance...',
            }),
            'capa_type': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'linked_incident': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe the non-conformance or issue in detail...',
            }),
            'impact_assessment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'What is the impact on patients, staff, or operations?',
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'target_completion_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CAPAInvestigationForm(forms.ModelForm):
    """Form for root cause analysis phase."""
    class Meta:
        model = CAPARecord
        fields = [
            'root_cause_method', 'root_cause_analysis',
            'root_cause_summary', 'contributing_factors',
        ]
        widgets = {
            'root_cause_method': forms.Select(attrs={'class': 'form-select'}),
            'root_cause_analysis': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': 'Document your root cause analysis findings...',
            }),
            'root_cause_summary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'One-line root cause summary...',
            }),
            'contributing_factors': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Additional contributing factors...',
            }),
        }


class CAPAActionPlanForm(forms.ModelForm):
    """Form for corrective and preventive action planning."""
    class Meta:
        model = CAPARecord
        fields = [
            'immediate_containment', 'corrective_action_plan',
            'preventive_action_plan', 'related_sops',
        ]
        widgets = {
            'immediate_containment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'What immediate actions were taken to contain the issue?',
            }),
            'corrective_action_plan': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': 'Detail the corrective actions to address the root cause...',
            }),
            'preventive_action_plan': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': 'What will be done to prevent recurrence?',
            }),
            'related_sops': forms.SelectMultiple(attrs={
                'class': 'form-select', 'size': 5,
            }),
        }


class CAPAVerificationForm(forms.ModelForm):
    """Form for effectiveness verification."""
    class Meta:
        model = CAPARecord
        fields = [
            'verification_criteria', 'verification_results', 'is_effective',
        ]
        widgets = {
            'verification_criteria': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'How will you verify the actions were effective?',
            }),
            'verification_results': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Document the results of your verification...',
            }),
            'is_effective': forms.Select(
                choices=[(None, '-- Select --'), (True, 'Yes — effective'),
                         (False, 'No — not effective, re-investigation needed')],
                attrs={'class': 'form-select'},
            ),
        }


class CAPACommentForm(forms.ModelForm):
    """Form for adding timeline comments."""
    class Meta:
        model = CAPAComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Add a comment or update...',
            }),
        }
