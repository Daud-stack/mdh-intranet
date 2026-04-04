from django.contrib import admin
from .models import SOP, SOPCategory

@admin.register(SOPCategory)
class SOPCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    search_fields = ('name',)

@admin.register(SOP)
class SOPAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'version', 'status', 'created_by', 'updated_at')
    list_filter = ('status', 'category', 'created_by')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
