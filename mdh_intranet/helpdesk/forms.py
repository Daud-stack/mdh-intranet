from django import forms
from django.contrib.auth.models import User
from .models import Ticket, TicketComment

class TicketForm(forms.ModelForm):
    """Simple form for user to create a ticket"""
    class Meta:
        model = Ticket
        fields = [
            'category', 'priority', 'title', 'description', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary e.g. "Printer jammed"'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description of the problem...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TicketUpdateForm(forms.ModelForm):
    """Full form for staff to manage ticket"""
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assignee', 'category']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show active staff OR members of 'IT Helpdesk' group
        from django.db.models import Q
        self.fields['assignee'].queryset = User.objects.filter(
            Q(is_staff=True) | Q(groups__name='IT Helpdesk'),
            is_active=True
        ).distinct()
        # Show full name
        self.fields['assignee'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})" if obj.get_full_name() else obj.username

class CommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['text', 'is_internal']
        labels = {'text': 'Reply'}
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a response...'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
