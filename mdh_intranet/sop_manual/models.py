from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SOPCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-folder', help_text="FontAwesome icon class")

    class Meta:
        verbose_name_plural = "SOP Categories"

    def __str__(self):
        return self.name

class SOP(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(SOPCategory, on_delete=models.CASCADE, related_name='sops')
    content = models.TextField(help_text="Main content of the SOP")
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    file_attachment = models.FileField(upload_to='sops/', blank=True, null=True, help_text="Direct upload (Legacy)")
    linked_document = models.ForeignKey('documents.Document', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_sops', help_text="Link to an existing document from the Documents section")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sops')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (v{self.version})"
