from django import forms
from .models import SOPDraft, SOPTemplate


class TemplateSelectForm(forms.Form):
    """Step 1: Select an SOP template."""
    template = forms.ModelChoiceField(
        queryset=SOPTemplate.objects.filter(is_active=True),
        widget=forms.HiddenInput(),
        required=True,
    )


class DraftMetadataForm(forms.ModelForm):
    """Step 2: Basic draft metadata."""
    class Meta:
        model = SOPDraft
        fields = ['title', 'target_category', 'version', 'referenced_incidents', 'referenced_capas']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. SOP-CLN-001: Hand Hygiene Protocol',
                'id': 'id_title',
            }),
            'target_category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_target_category',
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width: 120px;',
                'placeholder': '1.0',
                'id': 'id_version',
            }),
            'referenced_incidents': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'referenced_capas': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }


class SectionContentForm(forms.Form):
    """Dynamic form for filling in template sections."""
    def __init__(self, *args, sections=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sections:
            for section in sections:
                field_key = f"section_{section['key']}"
                self.fields[field_key] = forms.CharField(
                    label=section['label'],
                    required=section.get('required', False),
                    widget=forms.Textarea(attrs={
                        'class': 'form-control section-textarea',
                        'rows': section.get('rows', 5),
                        'placeholder': section.get('placeholder', ''),
                        'id': f'id_{field_key}',
                    }),
                    help_text=section.get('help_text', ''),
                )


class ICDCodeForm(forms.Form):
    """Form for adding/searching ICD-11 codes."""
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search ICD-11 codes by code or description...',
            'id': 'icd_search_input',
            'autocomplete': 'off',
        }),
    )
