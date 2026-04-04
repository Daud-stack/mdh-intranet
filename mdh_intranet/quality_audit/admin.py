from django.contrib import admin
from .models import AuditTemplate, AuditQuestion, AuditSubmission, AuditAnswer

class AuditQuestionInline(admin.TabularInline):
    model = AuditQuestion
    extra = 3

@admin.register(AuditTemplate)
class AuditTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'department_target', 'is_active', 'created_at')
    inlines = [AuditQuestionInline]
    search_fields = ('title', 'department_target')

class AuditAnswerInline(admin.TabularInline):
    model = AuditAnswer
    extra = 0
    readonly_fields = ('question',)

@admin.register(AuditSubmission)
class AuditSubmissionAdmin(admin.ModelAdmin):
    list_display = ('template', 'department_audited', 'auditor', 'score', 'conducted_at')
    list_filter = ('template', 'department_audited')
    inlines = [AuditAnswerInline]
