import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SOPTemplate(models.Model):
    """
    Pre-built SOP templates that guide staff through drafting.
    Each template defines required sections and OpsHub formatting rules.
    """
    CATEGORY_CHOICES = [
        ('clinical', 'Clinical Procedure'),
        ('nursing', 'Nursing Protocol'),
        ('laboratory', 'Laboratory Procedure'),
        ('pharmacy', 'Pharmacy Protocol'),
        ('admin', 'Administrative Procedure'),
        ('infection_control', 'Infection Control'),
        ('emergency', 'Emergency Response'),
        ('radiology', 'Radiology Procedure'),
        ('surgical', 'Surgical Procedure'),
        ('general', 'General Operations'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(help_text="Describe when this template should be used")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    icon = models.CharField(max_length=60, default='fas fa-file-alt', help_text="FontAwesome icon class")
    is_clinical = models.BooleanField(default=False, help_text="If True, ICD-11 code fields are shown")
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    # Template structure stored as JSON
    # Format: [{"key": "purpose", "label": "Purpose / Objective", "type": "textarea", "required": true, "placeholder": "...", "help_text": "..."}, ...]
    sections_json = models.TextField(
        default='[]',
        help_text="JSON array defining the template sections"
    )

    # OpsHub-specific formatting rules (JSON)
    # Format: {"requires_header_table": true, "requires_version": true, ...}
    formatting_rules_json = models.TextField(
        default='{}',
        help_text="JSON object defining OpsHub formatting requirements"
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def sections(self):
        try:
            return json.loads(self.sections_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @sections.setter
    def sections(self, value):
        self.sections_json = json.dumps(value)

    @property
    def formatting_rules(self):
        try:
            return json.loads(self.formatting_rules_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @formatting_rules.setter
    def formatting_rules(self, value):
        self.formatting_rules_json = json.dumps(value)


class SOPDraft(models.Model):
    """
    A draft SOP being authored via the assistant.
    Tracks the multi-step workflow from template selection to final publication.
    """
    STATUS_CHOICES = [
        ('template_selected', 'Template Selected'),
        ('drafting', 'Drafting in Progress'),
        ('icd_review', 'ICD-11 Review'),
        ('validating', 'Validation in Progress'),
        ('validated', 'Validated'),
        ('needs_revision', 'Needs Revision'),
        ('ready', 'Ready for Publication'),
        ('published', 'Published to SOP Manual'),
        ('discarded', 'Discarded'),
    ]

    title = models.CharField(max_length=200)
    template = models.ForeignKey(SOPTemplate, on_delete=models.SET_NULL, null=True, related_name='drafts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sop_drafts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='template_selected')

    # Target SOP category and version
    target_category = models.ForeignKey(
        'sop_manual.SOPCategory', on_delete=models.SET_NULL,
        null=True, blank=True, help_text="Target SOP Manual category for publication"
    )
    version = models.CharField(max_length=20, default='1.0')

    # ICD-11 codes associated with this draft (clinical SOPs)
    icd_codes_json = models.TextField(
        default='[]',
        help_text="JSON array of ICD-11 code objects [{code, description}]"
    )

    # Validation
    validation_score = models.IntegerField(default=0, help_text="0-100 validation score")
    last_validated_at = models.DateTimeField(null=True, blank=True)

    # Intelligence Context: Referenced system records
    referenced_incidents = models.ManyToManyField('incident_log.Incident', blank=True, related_name='sop_drafts')
    referenced_capas = models.ManyToManyField('capa.CAPARecord', blank=True, related_name='sop_drafts')

    # The final compiled HTML content
    compiled_content = models.TextField(blank=True, default='')

    # Link to published SOP (after publishing)
    published_sop = models.ForeignKey(
        'sop_manual.SOP', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='source_draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def icd_codes(self):
        try:
            return json.loads(self.icd_codes_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @icd_codes.setter
    def icd_codes(self, value):
        self.icd_codes_json = json.dumps(value)

    @property
    def is_clinical(self):
        return self.template and self.template.is_clinical

    @property
    def status_color(self):
        colors = {
            'template_selected': 'secondary',
            'drafting': 'info',
            'icd_review': 'purple',
            'validating': 'warning',
            'validated': 'success',
            'needs_revision': 'danger',
            'ready': 'primary',
            'published': 'success',
            'discarded': 'dark',
        }
        return colors.get(self.status, 'secondary')

    @property
    def status_icon(self):
        icons = {
            'template_selected': 'fas fa-file-alt',
            'drafting': 'fas fa-pen',
            'icd_review': 'fas fa-stethoscope',
            'validating': 'fas fa-spinner fa-spin',
            'validated': 'fas fa-check-circle',
            'needs_revision': 'fas fa-exclamation-triangle',
            'ready': 'fas fa-rocket',
            'published': 'fas fa-check-double',
            'discarded': 'fas fa-trash',
        }
        return icons.get(self.status, 'fas fa-file')

    @property
    def completion_percentage(self):
        """Calculate how many required sections are filled."""
        sections = self.sections.all()
        if not sections.exists():
            return 0
        filled = sections.filter(content__gt='').count()
        total = sections.count()
        return int((filled / total) * 100) if total > 0 else 0


class SOPDraftSection(models.Model):
    """
    Individual section content for a draft SOP.
    Mapped to template section definitions.
    """
    draft = models.ForeignKey(SOPDraft, on_delete=models.CASCADE, related_name='sections')
    section_key = models.CharField(max_length=50)
    section_label = models.CharField(max_length=200)
    content = models.TextField(blank=True, default='')
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ('draft', 'section_key')

    def __str__(self):
        return f"{self.draft.title} — {self.section_label}"


class ValidationResult(models.Model):
    """
    Individual validation check results for a draft.
    """
    SEVERITY_CHOICES = [
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('success', 'Pass'),
    ]

    draft = models.ForeignKey(SOPDraft, on_delete=models.CASCADE, related_name='validations')
    rule_code = models.CharField(max_length=50, help_text="e.g. FMT-001, ICD-REQ-001")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    field_name = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    suggestion = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['severity', 'rule_code']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.rule_code}: {self.message[:60]}"

    @property
    def severity_color(self):
        return {
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
            'success': 'success',
        }.get(self.severity, 'secondary')

    @property
    def severity_icon(self):
        return {
            'error': 'fas fa-times-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle',
            'success': 'fas fa-check-circle',
        }.get(self.severity, 'fas fa-circle')
