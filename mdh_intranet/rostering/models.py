from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ShiftTemplate(models.Model):
    name = models.CharField(max_length=100, help_text="e.g. 'Morning Shift', 'Night Shift'")
    start_time = models.TimeField()
    end_time = models.TimeField()
    color = models.CharField(max_length=7, default='#3b82f6', help_text="Hex color code for calendar UI")
    
    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class Roster(models.Model):
    department = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rosters')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.department} | {self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"

class Shift(models.Model):
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    template = models.ForeignKey(ShiftTemplate, on_delete=models.CASCADE)
    required_staff = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['date', 'template__start_time']

    def __str__(self):
        return f"{self.template.name} ({self.date})"

class ShiftAssignment(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_shifts')
    is_attended = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.username} on {self.shift}"

class ShiftSwapRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    assignment = models.ForeignKey(ShiftAssignment, on_delete=models.CASCADE, related_name='swap_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_swaps')
    requested_colleague = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_swaps')
    reason = models.TextField(help_text="Why do you need to swap this shift?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Swap Request: {self.requester.username} to {self.requested_colleague.username}"
