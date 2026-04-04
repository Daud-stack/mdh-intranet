"""
Core infrastructure models for OpsHub.
Provides: Audit Trail, Notification Centre, Approval Workflows,
          Global Search indexing, and SOP Acknowledgement tracking.
"""
import json
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


# ─── 1. AUDIT TRAIL ─────────────────────────────────────────────

class AuditLog(models.Model):
    """
    Immutable record of every significant action in the system.
    Captures who did what, when, to which object, and what changed.
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('submit', 'Submitted'),
        ('publish', 'Published'),
        ('acknowledge', 'Acknowledged'),
        ('login', 'Logged In'),
        ('export', 'Exported'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=300, blank=True)

    # Field-level change tracking (JSON)
    changes_json = models.TextField(
        default='{}',
        help_text='JSON: {"field": {"old": "...", "new": "..."}}'
    )

    module = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
        ]

    def __str__(self):
        return f"[{self.get_action_display()}] {self.object_repr} by {self.user} @ {self.timestamp:%Y-%m-%d %H:%M}"

    @property
    def changes(self):
        try:
            return json.loads(self.changes_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def action_color(self):
        return {
            'create': 'success', 'update': 'info', 'delete': 'danger',
            'approve': 'success', 'reject': 'danger', 'submit': 'primary',
            'publish': 'success', 'acknowledge': 'info',
            'login': 'secondary', 'export': 'warning',
        }.get(self.action, 'secondary')

    @property
    def action_icon(self):
        return {
            'create': 'fas fa-plus-circle', 'update': 'fas fa-edit',
            'delete': 'fas fa-trash', 'approve': 'fas fa-check-circle',
            'reject': 'fas fa-times-circle', 'submit': 'fas fa-paper-plane',
            'publish': 'fas fa-globe', 'acknowledge': 'fas fa-eye',
            'login': 'fas fa-sign-in-alt', 'export': 'fas fa-download',
        }.get(self.action, 'fas fa-circle')


# ─── 2. NOTIFICATION CENTRE ────────────────────────────────────

class Notification(models.Model):
    """
    In-app notifications for users. Triggered by approvals, SOP updates,
    ticket changes, leave decisions, etc.
    """
    TYPE_CHOICES = [
        ('approval', 'Approval Request'),
        ('approved', 'Request Approved'),
        ('rejected', 'Request Rejected'),
        ('sop_update', 'SOP Updated'),
        ('sop_review', 'SOP Review Due'),
        ('acknowledge', 'Acknowledgement Required'),
        ('incident', 'Incident Reported'),
        ('ticket', 'Helpdesk Update'),
        ('leave', 'Leave Update'),
        ('system', 'System Notice'),
        ('mention', 'You were mentioned'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    title = models.CharField(max_length=300)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True, help_text="URL to navigate to on click")
    icon = models.CharField(max_length=60, default='fas fa-bell')

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional link to the source object
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.recipient}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def type_color(self):
        return {
            'approval': 'warning', 'approved': 'success', 'rejected': 'danger',
            'sop_update': 'info', 'sop_review': 'warning',
            'acknowledge': 'primary', 'incident': 'danger',
            'ticket': 'info', 'leave': 'success',
            'system': 'secondary', 'mention': 'primary',
        }.get(self.notification_type, 'secondary')

    @property
    def type_icon(self):
        return {
            'approval': 'fas fa-clipboard-check', 'approved': 'fas fa-check-circle',
            'rejected': 'fas fa-times-circle', 'sop_update': 'fas fa-book',
            'sop_review': 'fas fa-clock', 'acknowledge': 'fas fa-eye',
            'incident': 'fas fa-exclamation-triangle', 'ticket': 'fas fa-headset',
            'leave': 'fas fa-plane-departure', 'system': 'fas fa-cog',
            'mention': 'fas fa-at',
        }.get(self.notification_type, 'fas fa-bell')


# ─── 3. APPROVAL WORKFLOW ENGINE ───────────────────────────────

class ApprovalWorkflow(models.Model):
    """
    A reusable multi-step approval pipeline attached to any object.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    # Generic link to the object being approved (SOP, leave, incident, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=300, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='submitted_workflows'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_step = models.PositiveIntegerField(default=1)
    total_steps = models.PositiveIntegerField(default=1)

    module = models.CharField(max_length=100, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', '-updated_at']),
        ]

    def __str__(self):
        return f"Workflow #{self.pk}: {self.object_repr} ({self.get_status_display()})"

    @property
    def status_color(self):
        return {
            'draft': 'secondary', 'pending': 'warning',
            'approved': 'success', 'rejected': 'danger',
            'cancelled': 'dark',
        }.get(self.status, 'secondary')

    @property
    def progress_pct(self):
        if self.total_steps == 0:
            return 0
        completed = self.steps.filter(status='approved').count()
        return int((completed / self.total_steps) * 100)

    def submit(self):
        """Submit the workflow for approval."""
        self.status = 'pending'
        self.submitted_at = timezone.now()
        self.save()
        # Notify first approver
        first_step = self.steps.filter(order=1).first()
        if first_step:
            Notification.objects.create(
                recipient=first_step.approver,
                notification_type='approval',
                priority='high',
                title=f'Approval Required: {self.object_repr}',
                message=f'{self.submitted_by.get_full_name() or self.submitted_by.username} submitted "{self.object_repr}" for your review.',
                link=f'/core/approvals/{self.pk}/',
                icon='fas fa-clipboard-check',
                content_type=self.content_type,
                object_id=self.object_id,
            )


class ApprovalStep(models.Model):
    """
    Individual step in an approval workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ]

    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField(default=1)
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='approval_steps'
    )
    role_label = models.CharField(
        max_length=100, blank=True,
        help_text="e.g. 'Department Head', 'Quality Officer', 'Director'"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)
    signature_hash = models.CharField(
        max_length=128, blank=True,
        help_text="SHA-256 hash as digital signature"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ('workflow', 'order')

    def __str__(self):
        return f"Step {self.order}: {self.approver} ({self.get_status_display()})"

    def approve(self, comments=''):
        """Approve this step and advance the workflow."""
        import hashlib
        self.status = 'approved'
        self.comments = comments
        self.acted_at = timezone.now()
        # Create digital signature
        sig_data = f"{self.approver.pk}|{self.workflow.pk}|{self.acted_at.isoformat()}|approved"
        self.signature_hash = hashlib.sha256(sig_data.encode()).hexdigest()
        self.save()

        workflow = self.workflow
        # Notify submitter
        Notification.objects.create(
            recipient=workflow.submitted_by,
            notification_type='approved',
            title=f'Step {self.order} Approved: {workflow.object_repr}',
            message=f'{self.approver.get_full_name() or self.approver.username} approved step {self.order}.',
            link=f'/core/approvals/{workflow.pk}/',
            icon='fas fa-check-circle',
        )

        # Check if there's a next step
        next_step = workflow.steps.filter(order=self.order + 1).first()
        if next_step:
            workflow.current_step = next_step.order
            workflow.save()
            # Notify next approver
            Notification.objects.create(
                recipient=next_step.approver,
                notification_type='approval',
                priority='high',
                title=f'Approval Required: {workflow.object_repr}',
                message=f'Step {next_step.order} is now pending your review.',
                link=f'/core/approvals/{workflow.pk}/',
                icon='fas fa-clipboard-check',
            )
        else:
            # All steps complete
            workflow.status = 'approved'
            workflow.completed_at = timezone.now()
            workflow.save()

    def reject(self, comments=''):
        """Reject this step and the entire workflow."""
        import hashlib
        self.status = 'rejected'
        self.comments = comments
        self.acted_at = timezone.now()
        sig_data = f"{self.approver.pk}|{self.workflow.pk}|{self.acted_at.isoformat()}|rejected"
        self.signature_hash = hashlib.sha256(sig_data.encode()).hexdigest()
        self.save()

        workflow = self.workflow
        workflow.status = 'rejected'
        workflow.completed_at = timezone.now()
        workflow.save()

        Notification.objects.create(
            recipient=workflow.submitted_by,
            notification_type='rejected',
            priority='high',
            title=f'Rejected: {workflow.object_repr}',
            message=f'{self.approver.get_full_name() or self.approver.username} rejected at step {self.order}. Reason: {comments}',
            link=f'/core/approvals/{workflow.pk}/',
            icon='fas fa-times-circle',
        )


# ─── 4. SOP ACKNOWLEDGEMENT ────────────────────────────────────

class SOPAcknowledgement(models.Model):
    """
    Track that staff have read and understood a specific SOP.
    Required for accreditation and compliance auditing.
    """
    sop = models.ForeignKey(
        'sop_manual.SOP', on_delete=models.CASCADE,
        related_name='acknowledgements'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sop_acknowledgements'
    )
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    comments = models.TextField(blank=True, help_text="Optional notes from the user")

    class Meta:
        unique_together = ('sop', 'user')
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f"{self.user} acknowledged {self.sop} on {self.acknowledged_at:%Y-%m-%d}"


class SOPReviewSchedule(models.Model):
    """
    Schedule periodic reviews for SOPs.
    Automatically generates notifications when review is due.
    """
    sop = models.OneToOneField(
        'sop_manual.SOP', on_delete=models.CASCADE,
        related_name='review_schedule'
    )
    review_interval_days = models.PositiveIntegerField(
        default=365, help_text="Days between reviews"
    )
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sop_reviews'
    )
    is_overdue = models.BooleanField(default=False)

    def __str__(self):
        return f"Review: {self.sop} (next: {self.next_review_at})"

    def check_overdue(self):
        if self.next_review_at and timezone.now() > self.next_review_at:
            self.is_overdue = True
            self.save(update_fields=['is_overdue'])
        return self.is_overdue
