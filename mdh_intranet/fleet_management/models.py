from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Vehicle(models.Model):
    TYPE_CHOICES = [
        ('AMBULANCE', 'Ambulance'),
        ('PATIENT_TRANSPORT', 'Patient Transport'),
        ('UTILITY', 'Utility / Delivery'),
        ('EXECUTIVE', 'Executive Staff'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('IN_TRANSIT', 'In Transit'),
        ('MAINTENANCE', 'In Maintenance'),
        ('OUT_OF_SERVICE', 'Out of Service'),
    ]

    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    license_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='AMBULANCE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    current_mileage = models.IntegerField(default=0, help_text="Current odometer reading in km")
    
    # Compliance
    registration_expiry = models.DateField()
    insurance_expiry = models.DateField()
    next_service_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-status', 'vehicle_type']

    def __str__(self):
        return f"{self.license_plate} - {self.get_vehicle_type_display()} ({self.make} {self.model})"

class TripLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='driven_trips')
    
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    start_mileage = models.IntegerField()
    end_mileage = models.IntegerField(null=True, blank=True)
    
    origin = models.CharField(max_length=150)
    destination = models.CharField(max_length=150)
    purpose = models.TextField()
    
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Trip {self.id}: {self.vehicle.license_plate} to {self.destination}"
        
class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    liters = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total cost in local currency")
    odometer = models.IntegerField()
    receipt = models.FileField(upload_to='fuel_receipts/', null=True, blank=True)
    
    def __str__(self):
        return f"Fuel: {self.vehicle.license_plate} on {self.date}"
