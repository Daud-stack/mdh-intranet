from django.contrib import admin
from .models import (
    AuditLog, Notification, ApprovalWorkflow, ApprovalStep,
    SOPAcknowledgement, SOPReviewSchedule,
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'module', 'object_repr')
    list_filter = ('action', 'module', 'timestamp')
    search_fields = ('object_repr', 'description', 'user__username')
    readonly_fields = ('user', 'action', 'timestamp', 'ip_address', 'content_type',
                       'object_id', 'object_repr', 'changes_json', 'module', 'description')
    date_hierarchy = 'timestamp'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read')
    search_fields = ('title', 'message', 'recipient__username')


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ('object_repr', 'status', 'submitted_by', 'module', 'current_step', 'total_steps', 'updated_at')
    list_filter = ('status', 'module')
    search_fields = ('object_repr', 'submitted_by__username')


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'order', 'approver', 'role_label', 'status', 'acted_at')
    list_filter = ('status',)
    search_fields = ('approver__username', 'role_label')


@admin.register(SOPAcknowledgement)
class SOPAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('sop', 'user', 'acknowledged_at')
    list_filter = ('acknowledged_at',)
    search_fields = ('sop__title', 'user__username')


@admin.register(SOPReviewSchedule)
class SOPReviewScheduleAdmin(admin.ModelAdmin):
    list_display = ('sop', 'review_interval_days', 'next_review_at', 'is_overdue')
    list_filter = ('is_overdue',)
