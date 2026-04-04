from django.contrib import admin
from .models import DocumentCategory, Document


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'document_count', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'uploaded_by', 'uploaded_at', 'file_size_formatted', 'downloads', 'is_public')
    list_filter = ('category', 'is_public', 'uploaded_at')
    search_fields = ('title', 'description')
    readonly_fields = ('uploaded_at', 'file_size', 'file_type', 'downloads')
