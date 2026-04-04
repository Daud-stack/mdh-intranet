"""
CAPA (Corrective & Preventive Action) Module Models.

Closes the quality loop:
  Incident / Non-Conformance → Root Cause Analysis → Corrective Action
  → Effectiveness Verification → Closure

Industry standard: ISO 9001:2015 §10.2, WHO quality guidelines.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class CAPARecord(models.Model):
    """
    Master record for a Corrective & Preventive Action.
    Can be linked to an incident or created standalone.
    """
    TYPE_CHOICES = [
        ('corrective', 'Corrective Action'),
        ('preventive', 'Preventive Action'),
        ('both', 'Corrective & Preventive'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('investigation', 'Under Investigation'),
        ('action_planning', 'Action Planning'),
        ('implementation', 'Implementation'),
        ('verification', 'Effectiveness Verification'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    SOURCE_CHOICES = [
        ('incident', 'Incident Report'),
        ('audit', 'Internal Audit'),
        ('complaint', 'Patient Complaint'),
        ('inspection', 'External Inspection'),
        ('observation', 'Staff Observation'),
        ('trend', 'Data Trend Analysis'),
        ('regulatory', 'Regulatory Requirement'),
        ('other', 'Other'),
    ]

    # ── Identity ──
    title = models.CharField(max_length=255)
    capa_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='corrective')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='incident')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # ── Link to Incident (optional) ──
    linked_incident = models.ForeignKey(
        'incident_log.Incident', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='capa_records',
        help_text="Originating incident (if applicable)"
    )

    # ── Description ──
    description = models.TextField(help_text="Detailed description of the non-conformance or issue")
    impact_assessment = models.TextField(
        blank=True,
        help_text="What is the impact on patients, staff, operations?"
    )

    # ── Root Cause Analysis ──
    root_cause_method = models.CharField(
        max_length=50, blank=True,
        choices=[
            ('5_whys', '5 Whys'),
            ('fishbone', 'Fishbone / Ishikawa'),
            ('fmea', 'FMEA'),
            ('pareto', 'Pareto Analysis'),
            ('fault_tree', 'Fault Tree Analysis'),
            ('other', 'Other'),
        ],
        help_text="Root cause analysis methodology used"
    )
    root_cause_analysis = models.TextField(
        blank=True,
        help_text="Detailed root cause analysis findings"
    )
    root_cause_summary = models.CharField(
        max_length=500, blank=True,
        help_text="One-line summary of the root cause"
    )
    contributing_factors = models.TextField(
        blank=True,
        help_text="Additional contributing factors"
    )

    # ── Corrective / Preventive Actions ──
    immediate_containment = models.TextField(
        blank=True,
        help_text="Immediate actions taken to contain the issue"
    )
    corrective_action_plan = models.TextField(
        blank=True,
        help_text="Detailed plan for corrective actions"
    )
    preventive_action_plan = models.TextField(
        blank=True,
        help_text="Actions to prevent recurrence"
    )

    # ── Effectiveness Verification ──
    verification_criteria = models.TextField(
        blank=True,
        help_text="How will we verify the actions were effective?"
    )
    verification_results = models.TextField(
        blank=True,
        help_text="Results of effectiveness verification"
    )
    is_effective = models.BooleanField(
        null=True, blank=True,
        help_text="Were the actions effective in resolving the issue?"
    )

    # ── People ──
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='initiated_capas'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_capas',
        help_text="Person responsible for this CAPA"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_capas',
        help_text="Person who verified effectiveness"
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='closed_capas'
    )

    # ── Dates ──
    target_completion_date = models.DateField(
        null=True, blank=True,
        help_text="Target date to complete all actions"
    )
    actual_completion_date = models.DateField(null=True, blank=True)
    verification_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Attachments ──
    attachment = models.FileField(
        upload_to='capa/%Y/%m/', null=True, blank=True,
        help_text="Supporting evidence or documentation"
    )

    # ── Related SOPs ──
    related_sops = models.ManyToManyField(
        'sop_manual.SOP', blank=True,
        related_name='related_capas',
        help_text="SOPs that need to be updated as a result"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'CAPA Record'
        verbose_name_plural = 'CAPA Records'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"CAPA-{self.pk:04d}: {self.title}"

    @property
    def capa_number(self):
        return f"CAPA-{self.pk:04d}"

    @property
    def is_overdue(self):
        if self.status not in ('closed', 'cancelled') and self.target_completion_date:
            return timezone.now().date() > self.target_completion_date
        return False

    @property
    def days_open(self):
        end = self.closed_at.date() if self.closed_at else timezone.now().date()
        return (end - self.created_at.date()).days

    @property
    def status_color(self):
        return {
            'draft': 'secondary',
            'investigation': 'info',
            'action_planning': 'warning',
            'implementation': 'primary',
            'verification': 'purple',
            'closed': 'success',
            'cancelled': 'dark',
        }.get(self.status, 'secondary')

    @property
    def status_icon(self):
        return {
            'draft': 'fas fa-file-alt',
            'investigation': 'fas fa-search',
            'action_planning': 'fas fa-clipboard-list',
            'implementation': 'fas fa-cogs',
            'verification': 'fas fa-check-double',
            'closed': 'fas fa-check-circle',
            'cancelled': 'fas fa-ban',
        }.get(self.status, 'fas fa-circle')

    @property
    def priority_color(self):
        return {
            'low': 'success',
            'medium': 'warning',
            'high': 'orange',
            'critical': 'danger',
        }.get(self.priority, 'secondary')

    @property
    def progress_pct(self):
        """Estimate progress based on status."""
        progress = {
            'draft': 5,
            'investigation': 20,
            'action_planning': 40,
            'implementation': 60,
            'verification': 85,
            'closed': 100,
            'cancelled': 0,
        }
        return progress.get(self.status, 0)

    def advance_status(self):
        """Move to the next logical status."""
        flow = ['draft', 'investigation', 'action_planning',
                'implementation', 'verification', 'closed']
        if self.status in flow:
            idx = flow.index(self.status)
            if idx < len(flow) - 1:
                self.status = flow[idx + 1]
                if self.status == 'closed':
                    self.closed_at = timezone.now()
                self.save()
                return True
        return False


class CAPAComment(models.Model):
    """Timeline comments on a CAPA record."""
    capa = models.ForeignKey(CAPARecord, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.capa.capa_number}"
