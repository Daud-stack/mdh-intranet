from django.contrib import admin
from .models import Asset, MaintenanceTask, WorkOrder, AssetReading, MaintenanceComment

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_id', 'category', 'location', 'status', 'criticality')
    list_filter = ('category', 'status', 'criticality')
    search_fields = ('name', 'asset_id', 'location')

@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'asset_category', 'frequency_days')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'asset', 'order_type', 'priority', 'status', 'assigned_to')
    list_filter = ('order_type', 'priority', 'status')
    search_fields = ('title', 'description', 'asset__name')

@admin.register(AssetReading)
class AssetReadingAdmin(admin.ModelAdmin):
    list_display = ('asset', 'reading_type', 'value', 'unit', 'timestamp')
    list_filter = ('reading_type', 'asset')
