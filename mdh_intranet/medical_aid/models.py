from django.db import models
from django.contrib.auth.models import User


class PreauthorizationRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    SCHEME_CHOICES = [
        ('PSMAS', 'PSMAS'),
        ('CIMAS', 'CIMAS'),
        ('FIRST_MUTUAL', 'First Mutual'),
        ('CELLMED', 'Cellmed'),
        ('FIDELITY', 'Fidelity Life'),
        ('MASCA', 'MASCA'),
        ('OTHER', 'Other'),
    ]

    # Default email addresses for each scheme (editable via admin or settings)
    SCHEME_EMAILS = {
        'PSMAS': 'preauth@psmas.co.zw',
        'CIMAS': 'preauth@cimas.co.zw',
        'FIRST_MUTUAL': 'preauth@firstmutual.co.zw',
        'CELLMED': 'preauth@cellmed.co.zw',
        'FIDELITY': 'preauth@fidelitylife.co.zw',
        'MASCA': 'preauth@masca.co.zw',
        'OTHER': '',
    }

    # ── Connections ──────────────────────────────────────────
    patient_link = models.ForeignKey('clinical.Patient', on_delete=models.SET_NULL, null=True, blank=True, related_name='preauth_requests')

    # ── Patient Details ──────────────────────────────────────
    patient_id = models.CharField(max_length=20, verbose_name='Patient/Member ID')
    patient_name = models.CharField(max_length=120, verbose_name='Patient Full Name', default='')
    patient_dob = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    patient_gender = models.CharField(
        max_length=10, blank=True,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        verbose_name='Gender'
    )
    patient_phone = models.CharField(max_length=20, blank=True, verbose_name='Contact Number')

    # ── Scheme / Insurance ───────────────────────────────────
    scheme = models.CharField(max_length=50, choices=SCHEME_CHOICES, verbose_name='Medical Aid Scheme')
    scheme_plan = models.CharField(max_length=60, blank=True, verbose_name='Plan / Tier')
    member_number = models.CharField(max_length=40, blank=True, verbose_name='Member Number')
    principal_name = models.CharField(max_length=120, blank=True, verbose_name='Principal Member Name')
    relationship = models.CharField(
        max_length=20, blank=True,
        choices=[('Self', 'Self'), ('Spouse', 'Spouse'), ('Child', 'Child'), ('Dependant', 'Dependant')],
        verbose_name='Relationship to Principal'
    )

    # ── Clinical Details ─────────────────────────────────────
    diagnosis = models.TextField(verbose_name='Diagnosis / Clinical Indication', default='')
    icd_code = models.CharField(max_length=20, blank=True, verbose_name='ICD-11 Code')
    procedure = models.CharField(max_length=200, verbose_name='Procedure / Treatment Requested')
    procedure_code = models.CharField(max_length=20, blank=True, verbose_name='Procedure Code (CPT)')
    clinical_notes = models.TextField(blank=True, verbose_name='Clinical Notes / Justification')
    is_emergency = models.BooleanField(default=False, verbose_name='Emergency Request')

    # ── Provider Details ─────────────────────────────────────
    referring_doctor = models.CharField(max_length=120, blank=True, verbose_name='Referring Doctor')
    attending_doctor = models.CharField(max_length=120, blank=True, verbose_name='Attending / Treating Doctor')
    facility_name = models.CharField(max_length=120, blank=True, verbose_name='Facility Name')

    # ── Financial ────────────────────────────────────────────
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Estimated Cost')
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('ZiG', 'ZiG')], default='USD')

    # ── Admin / Tracking ─────────────────────────────────────
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    supporting_document = models.FileField(upload_to='medical_aid/%Y/%m/', null=True, blank=True,
                                           verbose_name='Supporting Document')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='medical_aid_submissions')
    auth_number = models.CharField(max_length=40, blank=True, verbose_name='Auth Number (from Scheme)')
    notes = models.TextField(blank=True, verbose_name='Internal Notes')
    
    # ── Email Tracking ───────────────────────────────────────
    sent_to_email = models.EmailField(blank=True, verbose_name='Sent To Email')
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Email Sent At')
    email_sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='medical_aid_emails_sent')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Preauthorization Request'
        verbose_name_plural = 'Preauthorization Requests'

    def __str__(self):
        return f"{self.patient_id} - {self.patient_name} ({self.scheme})"

    @property
    def default_scheme_email(self):
        """Get the default email address for this request's scheme."""
        return self.SCHEME_EMAILS.get(self.scheme, '')
