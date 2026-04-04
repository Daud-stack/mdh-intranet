from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AuditTemplate(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department_target = models.CharField(max_length=150, help_text="e.g. ICU, General Ward, Pharmacy", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class AuditQuestion(models.Model):
    template = models.ForeignKey(AuditTemplate, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        
    def __str__(self):
        return f"{self.template.title} - Q: {self.text}"

class AuditSubmission(models.Model):
    template = models.ForeignKey(AuditTemplate, on_delete=models.CASCADE, related_name='submissions')
    auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conducted_audits')
    department_audited = models.CharField(max_length=150)
    conducted_at = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=0, help_text="Total score calculated from answers")
    notes = models.TextField(blank=True, help_text="General notes or observations")
    
    def __str__(self):
        return f"{self.template.title} in {self.department_audited} on {self.conducted_at.strftime('%Y-%m-%d')}"

class AuditAnswer(models.Model):
    submission = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(AuditQuestion, on_delete=models.CASCADE)
    passed = models.BooleanField(default=False)
    comments = models.TextField(blank=True)
    linked_capa = models.ForeignKey(
        'capa.CAPARecord', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='audit_findings'
    )
    
    def __str__(self):
        return f"{self.submission} - {'PASS' if self.passed else 'FAIL'}"
