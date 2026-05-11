from django import forms
from .models import Incident


class IncidentForm(forms.ModelForm):
    """Form for creating a new incident report."""
    class Meta:
        model = Incident
        fields = [
            'patient', 'involved_type', 'involved_employee', 'involved_contractor',
            'title', 'category', 'severity', 'priority',
            'location', 'date_occurred',
            'description', 'persons_involved', 'witnesses',
            'immediate_action', 'attachment',
        ]
        widgets = {
            'patient': forms.HiddenInput(),
            'involved_employee': forms.Select(attrs={'class': 'form-select'}),
            'involved_type': forms.Select(attrs={'class': 'form-select'}),
            'involved_contractor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Acme Maintenance Co.'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the incident',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ward B, Operating Theatre 3, Main Lobby',
            }),
            'date_occurred': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide a detailed account of what happened...',
            }),
            'persons_involved': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Names or IDs of people directly involved',
            }),
            'witnesses': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Names of any witnesses',
            }),
            'immediate_action': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What immediate steps were taken?',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_occurred'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['persons_involved'].required = False
        self.fields['witnesses'].required = False
        self.fields['immediate_action'].required = False


class IncidentUpdateForm(forms.ModelForm):
    """Form for updating an incident's status and resolution."""
    class Meta:
        model = Incident
        fields = [
            'status', 'severity', 'priority', 'assigned_to',
            'resolution_notes', 'corrective_actions', 'attachment',
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe how the incident was resolved...',
            }),
            'corrective_actions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Steps taken to prevent recurrence...',
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resolution_notes'].required = False
        self.fields['corrective_actions'].required = False
        self.fields['assigned_to'].required = False
