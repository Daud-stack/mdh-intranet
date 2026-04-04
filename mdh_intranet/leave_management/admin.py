from django.contrib import admin
from .models import LeaveType, LeaveRequest

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'days_per_year', 'is_active')
    search_fields = ('name',)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'leave_type', 'created_at')
    search_fields = ('user__username', 'reason', 'review_notes')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'leave_type', 'start_date', 'end_date', 'reason', 'attachment')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
