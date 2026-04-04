from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['category', 'subject', 'description', 'is_anonymous', 'attachment']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select rounded-3 border-light bg-light'}),
            'subject': forms.TextInput(attrs={'class': 'form-control rounded-3 border-light bg-light', 'placeholder': 'Summary of your suggestion'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-4 border-light bg-light', 'rows': 5, 'placeholder': 'Please provide as much detail as possible...'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'anonymousSwitch'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control rounded-3 border-light bg-light'}),
        }
