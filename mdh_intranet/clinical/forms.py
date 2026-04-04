from django import forms
from .models import Patient, Consultation, Prescription, LabRequest, PrescriptionItem, LabRequestItem, ImagingRequest, ImagingItem, TheatreBooking

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number', 'email', 'address', 'medical_aid_name', 'medical_aid_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['subjective', 'objective', 'assessment', 'plan', 'icd11_diagnosis']
        widgets = {
            'subjective': forms.Textarea(attrs={'rows': 4}),
            'objective': forms.Textarea(attrs={'rows': 4}),
            'assessment': forms.Textarea(attrs={'rows': 2}),
            'plan': forms.Textarea(attrs={'rows': 4}),
        }

class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ['medication_name', 'dosage', 'frequency', 'duration', 'total_quantity', 'instructions']

class LabRequestItemForm(forms.ModelForm):
    class Meta:
        model = LabRequestItem
        fields = ['test_name', 'specimen_type', 'notes']

class ImagingItemForm(forms.ModelForm):
    class Meta:
        model = ImagingItem
        fields = ['modality', 'view_area', 'clinical_question']

class TheatreBookingForm(forms.ModelForm):
    class Meta:
        model = TheatreBooking
        fields = ['procedure_name', 'priority', 'proposed_date', 'estimated_duration', 'assistant_surgeon', 'anaesthetist', 'theatre_notes']
        widgets = {
            'proposed_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

from .models import PatientVitals, PatientAllergy, ChronicCondition, NursingNote, FluidBalance, ShiftHandover

class PatientVitalsForm(forms.ModelForm):
    class Meta:
        model = PatientVitals
        fields = [
            'temperature', 'blood_pressure_sys', 'blood_pressure_dia', 
            'heart_rate', 'respiratory_rate', 'oxygen_saturation', 
            'weight_kg', 'height_cm', 'level_of_consciousness', 
            'is_trauma', 'mobility'
        ]

class NursingNoteForm(forms.ModelForm):
    class Meta:
        model = NursingNote
        fields = ['situation', 'background', 'assessment', 'recommendation', 'dressing_done', 'wound_care_notes', 'pain_score']
        widgets = {
            'situation': forms.Textarea(attrs={'rows': 2}),
            'background': forms.Textarea(attrs={'rows': 2}),
            'assessment': forms.Textarea(attrs={'rows': 2}),
            'recommendation': forms.Textarea(attrs={'rows': 2}),
        }

class FluidBalanceForm(forms.ModelForm):
    class Meta:
        model = FluidBalance
        fields = ['oral_intake', 'iv_intake', 'urine_output', 'drain_output', 'emesis']

class ShiftHandoverForm(forms.ModelForm):
    class Meta:
        model = ShiftHandover
        fields = ['incoming_nurse', 'shift_date', 'shift_type', 'patients', 'situation', 'background', 'assessment', 'recommendation', 'general_ward_notes']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'patients': forms.SelectMultiple(attrs={'class': 'select2'}),
            'situation': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ward status, staffing, major events...'}),
            'background': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Recent admissions/discharges, key history...'}),
            'assessment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Critical patients or clinical concerns...'}),
            'recommendation': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Tasks for the incoming shift...'}),
            'general_ward_notes': forms.Textarea(attrs={'rows': 2}),
        }

class PatientAllergyForm(forms.ModelForm):
    class Meta:
        model = PatientAllergy
        fields = ['allergen', 'severity', 'reaction']

class ChronicConditionForm(forms.ModelForm):
    class Meta:
        model = ChronicCondition
        fields = ['condition_name', 'diagnosed_date', 'status', 'notes']
        widgets = {
            'diagnosed_date': forms.DateInput(attrs={'type': 'date'}),
        }
