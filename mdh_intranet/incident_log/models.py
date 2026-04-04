from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Incident(models.Model):
    CATEGORY_CHOICES = [
        ('patient_fall', 'Patient Fall'),
        ('medication_error', 'Medication Error'),
        ('equipment_failure', 'Equipment Failure'),
        ('staff_injury', 'Staff Injury'),
        ('infection_control', 'Infection Control'),
        ('security_breach', 'Security Breach'),
        ('near_miss', 'Near Miss'),
        ('it_issue', 'IT / System Issue'),
        ('other', 'Other'),
    ]

    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Under Investigation', 'Under Investigation'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]

    # Core fields
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    location = models.CharField(max_length=100)
    date_occurred = models.DateTimeField(default=timezone.now, help_text="When the incident occurred")
    date_reported = models.DateTimeField(default=timezone.now)

    # People
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_incidents')
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_incidents',
        help_text="Staff member investigating this incident"
    )

    # Classification
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Low')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')

    # Involved parties
    persons_involved = models.TextField(blank=True, help_text="Names/IDs of people involved in the incident")
    witnesses = models.TextField(blank=True, help_text="Names of witnesses")

    # Actions & Resolution
    immediate_action = models.TextField(blank=True, help_text="Immediate action taken at the time")
    attachment = models.FileField(upload_to='incidents/%Y/%m/', null=True, blank=True, help_text="Upload evidence or photos")
    resolution_notes = models.TextField(blank=True, help_text="How the incident was resolved")
    corrective_actions = models.TextField(blank=True, help_text="Steps taken to prevent recurrence")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resolved_incidents'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"INC-{self.pk:03d}: {self.title} ({self.status})"

    @property
    def incident_number(self):
        return f"INC-{self.pk:03d}"

    @property
    def is_overdue(self):
        """An open incident older than 7 days is considered overdue."""
        if self.status in ('Open', 'Under Investigation'):
            return (timezone.now() - self.date_reported).days > 7
        return False

    class Meta:
        ordering = ['-date_reported']
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
