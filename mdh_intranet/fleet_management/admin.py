from django.contrib import admin
from .models import Vehicle, TripLog, FuelLog

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'make', 'model', 'vehicle_type', 'status', 'current_mileage')
    list_filter = ('vehicle_type', 'status')
    search_fields = ('license_plate', 'make', 'model')

@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'driver', 'origin', 'destination', 'start_time', 'end_time')
    search_fields = ('origin', 'destination', 'driver__username')

@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'liters', 'cost', 'odometer', 'logged_by')
