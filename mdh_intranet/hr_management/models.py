from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="e.g. Office, Remote, Field")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Attendance"
        unique_together = ('user', 'date')
        ordering = ['-date', '-clock_in']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class PerformanceReview(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    review_date = models.DateField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.employee.username} on {self.review_date}"

class TrainingRecord(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_records')
    course_name = models.CharField(max_length=200)
    provider = models.CharField(max_length=200, blank=True)
    completion_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    attachment = models.FileField(upload_to='training_certs/', blank=True, null=True)

    def __str__(self):
        return f"{self.course_name} - {self.employee.username}"


class HiringRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Position Filled'),
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hiring_requests')
    department = models.CharField(max_length=100)
    position_title = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=[
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ])
    reason = models.CharField(max_length=20, choices=[
        ('NEW', 'New Position'),
        ('REPLACEMENT', 'Replacement'),
    ])
    replacement_for = models.CharField(max_length=200, blank=True, null=True, help_text="If replacement, who are they replacing?")
    proposed_start_date = models.DateField()
    salary_range = models.CharField(max_length=100, blank=True)
    justification = models.TextField(help_text="Detailed justification for this hire")
    job_description = models.TextField()
    qualifications = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True, help_text="Notes from HR/Management")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position_title} - {self.department} ({self.get_status_display()})"
