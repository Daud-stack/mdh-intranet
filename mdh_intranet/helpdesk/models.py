from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('1_low', 'Low'),
        ('2_medium', 'Medium'),
        ('3_high', 'High'),
        ('4_critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    CATEGORY_CHOICES = [
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('network', 'Network / Internet'),
        ('access', 'Access / Permissions'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='2_medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    attachment = models.FileField(upload_to='tickets/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TK-{self.pk}: {self.title}"

    def save(self, *args, **kwargs):
        if self.status in ['resolved', 'closed'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status in ['open', 'in_progress']:
            self.resolved_at = None
        super().save(*args, **kwargs)

    @property
    def ticket_id(self):
        return f"TK-{self.pk:04d}"

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False, help_text="Visible only to staff")

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"
