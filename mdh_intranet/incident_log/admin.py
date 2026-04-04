from django.contrib import admin
from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'title', 'category', 'severity', 'status', 'reported_by', 'date_reported', 'is_overdue')
    list_filter = ('status', 'severity', 'category', 'priority')
    search_fields = ('title', 'description', 'location', 'reported_by__username')
    list_editable = ('status', 'severity')
    date_hierarchy = 'date_reported'
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('reported_by', 'assigned_to', 'resolved_by')

    fieldsets = (
        ('Incident Details', {
            'fields': ('title', 'category', 'description', 'location', 'date_occurred')
        }),
        ('Classification', {
            'fields': ('severity', 'status', 'priority')
        }),
        ('People', {
            'fields': ('reported_by', 'assigned_to', 'persons_involved', 'witnesses')
        }),
        ('Actions & Resolution', {
            'fields': ('immediate_action', 'resolution_notes', 'corrective_actions', 'resolved_at', 'resolved_by'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
