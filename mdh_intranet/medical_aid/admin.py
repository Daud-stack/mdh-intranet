from django.contrib import admin
from .models import PreauthorizationRequest


@admin.register(PreauthorizationRequest)
class PreauthorizationRequestAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'patient_name', 'scheme', 'procedure', 'status', 'is_emergency', 'created_at')
    list_filter = ('status', 'scheme', 'is_emergency', 'created_at')
    search_fields = ('patient_id', 'patient_name', 'scheme', 'procedure', 'diagnosis', 'member_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'patient_name', 'patient_dob', 'patient_gender', 'patient_phone')
        }),
        ('Insurance / Scheme', {
            'fields': ('scheme', 'scheme_plan', 'member_number', 'principal_name', 'relationship')
        }),
        ('Clinical Details', {
            'fields': ('diagnosis', 'icd_code', 'procedure', 'procedure_code', 'clinical_notes', 'is_emergency')
        }),
        ('Provider', {
            'fields': ('referring_doctor', 'attending_doctor', 'facility_name')
        }),
        ('Financial & Admin', {
            'fields': ('amount', 'currency', 'status', 'auth_number', 'supporting_document', 'submitted_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
