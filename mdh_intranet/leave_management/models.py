from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class LeaveType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    days_per_year = models.IntegerField(default=21)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    attachment = models.FileField(upload_to='leave_attachments/%Y/%m/', null=True, blank=True)
    
    # Review fields
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    @property
    def duration(self):
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days + 1
        return 0
