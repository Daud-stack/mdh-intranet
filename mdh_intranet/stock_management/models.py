from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StockCategory(models.Model):
    """Categories for organizing stock items"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Stock Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StockItem(models.Model):
    """Individual stock items with inventory tracking"""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(StockCategory, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, help_text="e.g., box, bottle, unit, pack")
    current_quantity = models.IntegerField(default=0)
    min_threshold = models.IntegerField(default=10, help_text="Alert when stock falls below this")
    max_threshold = models.IntegerField(default=100)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.unit})"
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum threshold"""
        return self.current_quantity <= self.min_threshold
    
    @property
    def stock_status(self):
        """Get stock status label"""
        if self.current_quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"


class Requisition(models.Model):
    """Internal requests for stock items"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('fulfilled', 'Fulfilled'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('clinical', 'Clinical'),
        ('nursing', 'Nursing'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('admin', 'Administration'),
        ('maintenance', 'Maintenance'),
        ('housekeeping', 'Housekeeping'),
    ]
    
    requisition_number = models.CharField(max_length=50, unique=True, editable=False)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    justification = models.TextField(help_text="Explain why these items are needed")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requisitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.requisition_number} - {self.get_department_display()}"
    
    def save(self, *args, **kwargs):
        if not self.requisition_number:
            # Generate requisition number: REQ-YYYYMMDD-XXX
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = Requisition.objects.filter(
                requisition_number__startswith=f'REQ-{date_str}'
            ).count() + 1
            self.requisition_number = f'REQ-{date_str}-{count:03d}'
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Count total line items"""
        return self.items.count()
    
    @property
    def can_approve(self):
        """Check if requisition can be approved"""
        return self.status == 'pending'


class RequisitionItem(models.Model):
    """Line items in a requisition"""
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_approved = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.stock_item.name} x {self.quantity_requested}"
    
    @property
    def approved_quantity(self):
        """Get approved quantity or requested if not yet approved"""
        return self.quantity_approved if self.quantity_approved is not None else self.quantity_requested


class StockOrder(models.Model):
    """External purchase orders for stock"""
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    supplier = models.CharField(max_length=200)
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-order_date']
    
    def __str__(self):
        return f"{self.order_number} - {self.supplier}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: PO-YYYYMMDD-XXX
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = StockOrder.objects.filter(
                order_number__startswith=f'PO-{date_str}'
            ).count() + 1
            self.order_number = f'PO-{date_str}-{count:03d}'
        super().save(*args, **kwargs)
