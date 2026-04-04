from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os


class DocumentCategory(models.Model):
    """Categories for organizing documents"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-file', help_text="FontAwesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def document_count(self):
        return self.documents.count()


class Document(models.Model):
    """Uploadable documents with metadata"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
                              'txt', 'csv', 'zip', 'jpg', 'png', 'gif']
        )]
    )
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    file_type = models.CharField(max_length=10, blank=True)
    downloads = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True, help_text="If unchecked, only staff can access")
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-populate file_size and file_type before saving"""
        if self.file:
            self.file_size = self.file.size
            # Get file extension
            file_ext = os.path.splitext(self.file.name)[1][1:].lower()
            self.file_type = file_ext
        super().save(*args, **kwargs)
    
    @property
    def file_size_formatted(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def file_icon(self):
        """Return appropriate FontAwesome icon based on file type"""
        icon_map = {
            'pdf': 'fa-file-pdf text-danger',
            'doc': 'fa-file-word text-primary',
            'docx': 'fa-file-word text-primary',
            'xls': 'fa-file-excel text-success',
            'xlsx': 'fa-file-excel text-success',
            'ppt': 'fa-file-powerpoint text-warning',
            'pptx': 'fa-file-powerpoint text-warning',
            'txt': 'fa-file-alt text-secondary',
            'csv': 'fa-file-csv text-success',
            'zip': 'fa-file-archive text-info',
            'jpg': 'fa-file-image text-info',
            'png': 'fa-file-image text-info',
            'gif': 'fa-file-image text-info',
        }
        return icon_map.get(self.file_type, 'fa-file text-secondary')
