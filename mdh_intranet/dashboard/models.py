from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ALERT', 'Alert'),
    ]

    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_posted']
