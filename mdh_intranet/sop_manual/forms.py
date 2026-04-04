from django import forms
from .models import SOP

class SOPForm(forms.ModelForm):
    class Meta:
        model = SOP
        fields = ['title', 'category', 'status', 'version', 'content', 'linked_document', 'file_attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100px;'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'id': 'sop_content_editor'}),
            'linked_document': forms.Select(attrs={'class': 'form-select'}),
            'file_attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
