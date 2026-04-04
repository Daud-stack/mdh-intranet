from django.db import models
from django.contrib.auth.models import User

class ICDCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    chapter = models.CharField(max_length=100)
    block = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.description}"

    class Meta:
        ordering = ['code']
        verbose_name = "ICD Code"
        verbose_name_plural = "ICD Codes"

class RecentlyViewedCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.ForeignKey(ICDCode, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']
        unique_together = ('user', 'code') # Ensure one record per user-code pair, update timestamp on re-view
