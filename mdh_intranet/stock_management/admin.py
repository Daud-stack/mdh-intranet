from django.contrib import admin
from .models import StockCategory, StockItem, Requisition, RequisitionItem, StockOrder


@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_quantity', 'unit', 'stock_status', 'unit_cost']
    list_filter = ['category']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


class RequisitionItemInline(admin.TabularInline):
    model = RequisitionItem
    extra = 1


@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = ['requisition_number', 'department', 'requested_by', 'status', 'created_at']
    list_filter = ['status', 'department', 'created_at']
    search_fields = ['requisition_number', 'requested_by__username']
    readonly_fields = ['requisition_number', 'created_at', 'approved_at']
    inlines = [RequisitionItemInline]


@admin.register(StockOrder)
class StockOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'order_date', 'status', 'total_cost']
    list_filter = ['status', 'order_date']
    search_fields = ['order_number', 'supplier']
    readonly_fields = ['order_number', 'created_at']
