from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Asset(models.Model):
    STATUS_CHOICES = [
        ('OPERATIONAL', 'Operational'),
        ('DOWN', 'Out of Service'),
        ('MAINTENANCE', 'In Maintenance'),
        ('RETIRED', 'Retired'),
    ]
    
    CRITICALITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    name = models.CharField(max_length=200)
    asset_id = models.CharField(max_length=50, unique=True, verbose_name="Asset Tag / ID")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Manufacturer Serial Number")
    category = models.CharField(max_length=100, help_text="e.g. HVAC, Lab Equip, Electrical")
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPERATIONAL')
    criticality = models.CharField(max_length=20, choices=CRITICALITY_CHOICES, default='MEDIUM')
    
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    next_ppm_date = models.DateField(null=True, blank=True)
    
    specifications = models.TextField(blank=True)
    manual_url = models.URLField(blank=True, verbose_name="Link to Manual")
    
    def __str__(self):
        return f"{self.name} ({self.asset_id})"

class MaintenanceTask(models.Model):
    """PPM (Planned Preventive Maintenance) Template"""
    asset_category = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    frequency_days = models.IntegerField(help_text="Days between service (e.g. 30 for monthly)")
    estimated_duration_mins = models.IntegerField(default=60)
    
    def __str__(self):
        return f"{self.title} (Every {self.frequency_days} days)"

class WorkOrder(models.Model):
    TYPE_CHOICES = [
        ('PPM', 'Planned Preventive'),
        ('REACTIVE', 'Corrective/Repair'),
        ('PREDICTIVE', 'Predictive Alert'),
        ('UPGRADE', 'Upgrade/Install'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EMERGENCY', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open/New'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold/Waiting Parts'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='work_orders')
    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='REACTIVE')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_maintenance')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"WO#{self.id} - {self.title} ({self.status})"

class AssetReading(models.Model):
    """Predictive maintenance data points"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='readings')
    reading_type = models.CharField(max_length=50, help_text="e.g. Temperature, Runtime, Pressure")
    value = models.FloatField()
    unit = models.CharField(max_length=10)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.asset.name} - {self.reading_type}: {self.value}{self.unit}"

class MaintenanceComment(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='maintenance_attachments/', blank=True, null=True)
