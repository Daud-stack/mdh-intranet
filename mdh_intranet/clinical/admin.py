from django.contrib import admin
from .models import (
    Patient, Consultation, Prescription, PrescriptionItem, 
    LabRequest, LabRequestItem, ImagingRequest, ImagingItem, TheatreBooking,
    PatientVitals, PatientAllergy, ChronicCondition,
    Medication, DrugInteraction, NursingNote, FluidBalance, ShiftHandover
)

@admin.register(NursingNote)
class NursingNoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'nurse', 'recorded_at', 'pain_score')
    list_filter = ('recorded_at', 'nurse')

@admin.register(FluidBalance)
class FluidBalanceAdmin(admin.ModelAdmin):
    list_display = ('patient', 'recorded_at', 'net_balance')

@admin.register(ShiftHandover)
class ShiftHandoverAdmin(admin.ModelAdmin):
    list_display = ('shift_date', 'shift_type', 'outgoing_nurse', 'incoming_nurse', 'is_completed')

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    fields = ('medication', 'medication_name', 'dosage', 'frequency', 'duration')
    extra = 0

class LabRequestItemInline(admin.TabularInline):
    model = LabRequestItem
    extra = 0

class ImagingItemInline(admin.TabularInline):
    model = ImagingItem
    extra = 0

class VitalsInline(admin.TabularInline):
    model = PatientVitals
    extra = 0

class AllergyInline(admin.TabularInline):
    model = PatientAllergy
    extra = 0

class ChronicConditionInline(admin.TabularInline):
    model = ChronicCondition
    extra = 0

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender', 'medical_aid_name')
    search_fields = ('first_name', 'last_name', 'medical_aid_number')
    list_filter = ('gender', 'medical_aid_name')
    inlines = [VitalsInline, AllergyInline, ChronicConditionInline]

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'gp', 'date', 'icd11_diagnosis')
    list_filter = ('date', 'gp')
    search_fields = ('patient__last_name', 'icd11_diagnosis')
    date_hierarchy = 'date'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'prescribed_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [PrescriptionItemInline]

@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'urgency', 'status', 'created_at')
    list_filter = ('urgency', 'status', 'created_at')
    inlines = [LabRequestItemInline]

@admin.register(ImagingRequest)
class ImagingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'urgency', 'status', 'created_at')
    list_filter = ('urgency', 'status', 'created_at')
    inlines = [ImagingItemInline]

@admin.register(TheatreBooking)
class TheatreBookingAdmin(admin.ModelAdmin):
    list_display = ('procedure_name', 'patient', 'proposed_date', 'priority', 'status')
    list_filter = ('priority', 'status', 'proposed_date')
    search_fields = ('procedure_name', 'patient__last_name')

@admin.register(PatientVitals)
class PatientVitalsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'recorded_at', 'recorded_by', 'blood_pressure_sys', 'blood_pressure_dia', 'temperature')

@admin.register(PatientAllergy)
class PatientAllergyAdmin(admin.ModelAdmin):
    list_display = ('patient', 'allergen', 'severity', 'recorded_at')

@admin.register(ChronicCondition)
class ChronicConditionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'condition_name', 'status', 'diagnosed_date')

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'drug_class')
    search_fields = ('name', 'generic_name')

@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    list_display = ('drug_a', 'drug_b', 'severity')
    list_filter = ('severity',)
