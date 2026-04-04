from django import forms
from .models import Document, DocumentCategory


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents"""
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_public': 'Public Access (uncheck for staff-only)',
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 10MB.')
        return file


class SOPGeneratorForm(forms.Form):
    """Form for generating Standard Operating Procedures"""
    category = forms.ModelChoiceField(queryset=DocumentCategory.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    
    # Metadata
    sop_title = forms.CharField(label="SOP Title", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sop_code = forms.CharField(label="SOP Code", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SOP-HR-001'}), initial="SOP-")
    version = forms.CharField(label="Version", widget=forms.TextInput(attrs={'class': 'form-control'}), initial="1.0")
    department = forms.CharField(label="Department", widget=forms.TextInput(attrs={'class': 'form-control'}))
    effective_date = forms.DateField(label="Effective Date", widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    
    # Approvals
    created_by = forms.CharField(label="Created By", widget=forms.TextInput(attrs={'class': 'form-control'}))
    approved_by = forms.CharField(label="Approved By", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Content
    purpose = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    scope = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    definitions = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional definitions...'}))
    materials = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional materials...'}))
    
    procedure = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Step 1...\nStep 2...'}))
    
    high_alert = forms.CharField(required=False, label="High-Alert Handling", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    safety = forms.CharField(required=False, label="Safety Precautions", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    documentation = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    references = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
