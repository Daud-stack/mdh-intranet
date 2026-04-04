from django.contrib import admin
from .models import SOPTemplate, SOPDraft, SOPDraftSection, ValidationResult


class SOPDraftSectionInline(admin.TabularInline):
    model = SOPDraftSection
    extra = 0


class ValidationResultInline(admin.TabularInline):
    model = ValidationResult
    extra = 0
    readonly_fields = ('rule_code', 'severity', 'field_name', 'message', 'suggestion', 'is_resolved')


@admin.register(SOPTemplate)
class SOPTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_clinical', 'is_active', 'usage_count', 'created_at')
    list_filter = ('is_clinical', 'is_active', 'category')
    search_fields = ('name', 'description')


@admin.register(SOPDraft)
class SOPDraftAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'author', 'status', 'validation_score', 'updated_at')
    list_filter = ('status', 'template')
    search_fields = ('title',)
    inlines = [SOPDraftSectionInline, ValidationResultInline]


@admin.register(ValidationResult)
class ValidationResultAdmin(admin.ModelAdmin):
    list_display = ('draft', 'rule_code', 'severity', 'field_name', 'is_resolved')
    list_filter = ('severity', 'is_resolved', 'rule_code')
