from django.contrib import admin
from .models import CAPARecord, CAPAComment


class CAPACommentInline(admin.TabularInline):
    model = CAPAComment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(CAPARecord)
class CAPARecordAdmin(admin.ModelAdmin):
    list_display = ('capa_number', 'title', 'capa_type', 'status', 'priority',
                    'assigned_to', 'target_completion_date', 'is_overdue')
    list_filter = ('status', 'capa_type', 'priority', 'source')
    search_fields = ('title', 'description', 'root_cause_summary')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    inlines = [CAPACommentInline]
    date_hierarchy = 'created_at'
