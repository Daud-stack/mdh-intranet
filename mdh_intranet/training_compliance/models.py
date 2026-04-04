from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TrainingCourse(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_mandatory = models.BooleanField(default=False, help_text="Is this course mandatory for all clinical staff?")
    validity_months = models.IntegerField(default=12, help_text="Months until certification expires. Set to 0 if it never expires.")
    
    provider = models.CharField(max_length=200, blank=True, null=True, help_text="Internal or External provider name")
    training_materials = models.FileField(upload_to='training_materials/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} {'(Mandatory)' if self.is_mandatory else ''}"

class Certification(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='certifications')
    
    date_completed = models.DateField(default=timezone.now)
    expiry_date = models.DateField(blank=True, null=True)
    
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-calculate expiry date if not explicitly set and course has validity period
        if not self.expiry_date and self.course.validity_months > 0:
            import datetime
            days_to_add = self.course.validity_months * 30 # Rough approximation
            self.expiry_date = self.date_completed + datetime.timedelta(days=days_to_add)
        super().save(*args, **kwargs)

    def is_expired(self):
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date

    def __str__(self):
        return f"{self.employee.username} - {self.course.title}"
