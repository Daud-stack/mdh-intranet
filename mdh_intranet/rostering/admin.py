from django.contrib import admin
from .models import ShiftTemplate, Roster, Shift, ShiftAssignment, ShiftSwapRequest

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'color')

class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 1

@admin.register(Roster)
class RosterAdmin(admin.ModelAdmin):
    list_display = ('department', 'start_date', 'end_date', 'is_published')
    list_filter = ('department', 'is_published')
    inlines = [ShiftInline]

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('template', 'date', 'roster', 'required_staff')
    list_filter = ('roster', 'template')

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shift', 'employee', 'is_attended')
    list_filter = ('is_attended', 'shift__date')

@admin.register(ShiftSwapRequest)
class ShiftSwapRequestAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'requester', 'requested_colleague', 'status', 'created_at')
    list_filter = ('status',)
