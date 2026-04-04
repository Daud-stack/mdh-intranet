from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Planning', 'Planning'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    progress = models.IntegerField(default=0, help_text="Progress in % (0-100)")
    
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projects')
    members = models.ManyToManyField(User, related_name='project_memberships', blank=True)
    attachment = models.FileField(upload_to='projects/%Y/%m/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-updated_at']
