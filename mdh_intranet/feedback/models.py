from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):
    CATEGORY_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('process', 'Process Improvement'),
        ('safety', 'Equipment & Safety'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='feedback/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category}: {self.subject}"
