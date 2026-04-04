from django import forms
from django.utils import timezone
from .models import Attendance, PerformanceReview, TrainingRecord, HiringRequest
from django.contrib.auth.models import User
from mdh_intranet.user_management.models import UserProfile

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['review_date', 'rating', 'strengths', 'areas_for_improvement', 'goals', 'comments']
        widgets = {
            'review_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ['course_name', 'provider', 'completion_date', 'expiry_date', 'certificate_number', 'attachment']
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'provider': forms.TextInput(attrs={'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

class StaffCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    # Profile fields
    role = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    employee_id = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    join_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set a default password if not provided (for simplicity in this flow, they can change it later)
        # In a real app, you'd send an email with a reset link
        user.set_password('MDHhub2026!') 
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data.get('role')
            profile.department = self.cleaned_data.get('department')
            profile.employee_id = self.cleaned_data.get('employee_id')
            profile.phone_number = self.cleaned_data.get('phone_number')
            profile.join_date = self.cleaned_data.get('join_date') or timezone.now().date()
            profile.save()
        return user

class HiringRequestForm(forms.ModelForm):
    class Meta:
        model = HiringRequest
        fields = [
            'position_title', 'department', 'employment_type', 
            'reason', 'replacement_for', 'proposed_start_date', 
            'salary_range', 'justification', 'job_description', 'qualifications'
        ]
        widgets = {
            'position_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'replacement_for': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional if new position'}),
            'proposed_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. $2000 - $3000'}),
            'justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
