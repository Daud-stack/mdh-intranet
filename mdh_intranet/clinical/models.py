from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    medical_aid_name = models.CharField(max_length=100, blank=True)
    medical_aid_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    gp = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gp_consultations')
    date = models.DateTimeField(default=timezone.now)
    
    # SOAP Notes
    subjective = models.TextField(verbose_name="Subjective (Patient's complaints)")
    objective = models.TextField(verbose_name="Objective (Physical findings)")
    assessment = models.TextField(verbose_name="Assessment (Diagnosis/ICD-11)")
    plan = models.TextField(verbose_name="Plan (Treatments/Referrals)")
    
    icd11_diagnosis = models.CharField(max_length=20, blank=True, help_text="Primary ICD-11 code")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation: {self.patient} on {self.date.date()}"

class Medication(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    drug_class = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.generic_name})"

class DrugInteraction(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major / Contraindicated'),
    ]
    drug_a = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_a')
    drug_b = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_b')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    warning_message = models.TextField()

    class Meta:
        unique_together = ('drug_a', 'drug_b')

    def __str__(self):
        return f"Interaction: {self.drug_a} + {self.drug_b}"

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Dispensing'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescriptions')
    prescribed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescribed_by')
    pharmacy_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Digital Signature for Pharmacist
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_by')
    dispensed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prescription #{self.pk} for {self.consultation.patient}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.SET_NULL, null=True, blank=True)
    medication_name = models.CharField(max_length=200, help_text="Used if Medication model is not selected")
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    total_quantity = models.CharField(max_length=50)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medication_name} ({self.dosage})"

class LabRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('collecting', 'Sample Collecting'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='lab_requests')
    gp = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gp_lab_requests')
    clinical_history = models.TextField(blank=True)
    urgency = models.CharField(max_length=20, choices=[('normal', 'Normal'), ('urgent', 'Urgent'), ('stat', 'STAT')], default='normal')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    results_ready = models.BooleanField(default=False)
    results_url = models.URLField(blank=True, help_text="Link to result document")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lab Request #{self.pk} for {self.consultation.patient}"

class LabRequestItem(models.Model):
    lab_request = models.ForeignKey(LabRequest, on_delete=models.CASCADE, related_name='test_items')
    test_name = models.CharField(max_length=200)
    specimen_type = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.test_name

class ImagingRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('scheduled', 'Scheduled'),
        ('capturing', 'Ongoing Capture'),
        ('interpreting', 'Interpretation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='imaging_requests')
    gp = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gp_imaging_requests')
    urgency = models.CharField(max_length=20, choices=[('normal', 'Normal'), ('urgent', 'Urgent'), ('stat', 'STAT')], default='normal')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    report_ready = models.BooleanField(default=False)
    results_url = models.URLField(blank=True, help_text="Link to DICOM/PACS viewer")
    report_file = models.FileField(upload_to='clinical/imaging_reports/', null=True, blank=True)
    imaging_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Imaging Request #{self.pk} for {self.consultation.patient}"

class ImagingItem(models.Model):
    imaging_request = models.ForeignKey(ImagingRequest, on_delete=models.CASCADE, related_name='items')
    modality = models.CharField(max_length=100, choices=[
        ('xray', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('other', 'Other'),
    ])
    view_area = models.CharField(max_length=200, help_text="e.g. Chest AP/Lateral, Right Knee")
    clinical_question = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_modality_display()}: {self.view_area}"

class TheatreBooking(models.Model):
    PRIORITY_CHOICES = [
        ('elective', 'Elective'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('pre-op', 'Pre-Op Preparation'),
        ('in-theatre', 'In Theatre'),
        ('post-op', 'Post-Op / Recovery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='theatre_bookings')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    procedure_name = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='elective')
    proposed_date = models.DateTimeField()
    estimated_duration = models.IntegerField(help_text="Estimated minutes", default=60)
    
    # Surgical Team
    surgeon = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surgeon_theatre_bookings')
    assistant_surgeon = models.CharField(max_length=255, blank=True)
    anaesthetist = models.CharField(max_length=255, blank=True)
    
    # Theatre Specifics
    theatre_number = models.CharField(max_length=50, blank=True)
    theatre_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PatientVitals(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    
    temperature = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Temp (°C)", null=True, blank=True)
    blood_pressure_sys = models.IntegerField(verbose_name="Systolic BP (mmHg)", null=True, blank=True)
    blood_pressure_dia = models.IntegerField(verbose_name="Diastolic BP (mmHg)", null=True, blank=True)
    heart_rate = models.IntegerField(verbose_name="Heart Rate (bpm)", null=True, blank=True)
    respiratory_rate = models.IntegerField(verbose_name="Resp Rate (breaths/min)", null=True, blank=True)
    oxygen_saturation = models.IntegerField(verbose_name="SpO2 (%)", null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Weight (kg)", null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Height (cm)", null=True, blank=True)
    
    # SATS Scoring Fields
    LOC_CHOICES = [('A', 'Alert'), ('V', 'Voice'), ('P', 'Pain'), ('U', 'Unresponsive')]
    level_of_consciousness = models.CharField(max_length=1, choices=LOC_CHOICES, default='A')
    is_trauma = models.BooleanField(default=False)
    mobility = models.CharField(max_length=20, choices=[('walking', 'Walking'), ('with_help', 'With Help'), ('stretcher', 'Stretcher/Immobile')], default='walking')
    
    @property
    def triage_score(self):
        """Calculates TEWS (Triage Early Warning Score) based on SATS guidelines."""
        score = 0
        
        # 1. Heart Rate
        if self.heart_rate:
            if self.heart_rate < 40: score += 3
            elif 41 <= self.heart_rate <= 50: score += 1
            elif 51 <= self.heart_rate <= 100: score += 0
            elif 101 <= self.heart_rate <= 110: score += 1
            elif 111 <= self.heart_rate <= 129: score += 2
            elif self.heart_rate >= 130: score += 3

        # 2. Systolic BP
        if self.blood_pressure_sys:
            if self.blood_pressure_sys < 70: score += 3
            elif 71 <= self.blood_pressure_sys <= 80: score += 2
            elif 81 <= self.blood_pressure_sys <= 100: score += 1
            elif 101 <= self.blood_pressure_sys <= 199: score += 0
            elif self.blood_pressure_sys >= 200: score += 2

        # 3. Respiratory Rate
        if self.respiratory_rate:
            if self.respiratory_rate < 9: score += 3
            elif 9 <= self.respiratory_rate <= 14: score += 0
            elif 15 <= self.respiratory_rate <= 20: score += 1
            elif 21 <= self.respiratory_rate <= 29: score += 2
            elif self.respiratory_rate >= 30: score += 3

        # 4. Temperature
        if self.temperature:
            if self.temperature < 35: score += 2
            elif 35 <= self.temperature <= 38.4: score += 0
            elif self.temperature >= 38.5: score += 1

        # 5. AVPU (Level of consciousness)
        if self.level_of_consciousness != 'A':
            score += 3
            
        # 6. Trauma / Mobility
        if self.mobility == 'stretcher': score += 2
        elif self.mobility == 'with_help': score += 1
        
        if self.is_trauma: score += 1
        
        return score

    @property
    def triage_color(self):
        score = self.triage_score
        if score == 0: return 'green'
        if 1 <= score <= 2: return 'yellow'
        if 3 <= score <= 6: return 'orange'
        return 'red'

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(float(self.weight_kg) / float(height_m * height_m), 1)
        return None

    class Meta:
        verbose_name_plural = "Patient Vitals"
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.patient} at {self.recorded_at}"

class NursingNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='nursing_notes')
    nurse = models.ForeignKey(User, on_delete=models.CASCADE)
    recorded_at = models.DateTimeField(default=timezone.now)
    
    # SBAR Format
    situation = models.TextField()
    background = models.TextField(blank=True)
    assessment = models.TextField()
    recommendation = models.TextField()
    
    # General Nursing
    dressing_done = models.BooleanField(default=False)
    wound_care_notes = models.TextField(blank=True)
    pain_score = models.IntegerField(null=True, blank=True, help_text="0-10 Scale")

    def __str__(self):
        return f"Nurse Note: {self.patient} by {self.nurse} at {self.recorded_at}"

class FluidBalance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='fluid_balances')
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Intake
    oral_intake = models.IntegerField(default=0, help_text="ml")
    iv_intake = models.IntegerField(default=0, help_text="ml")
    
    # Output
    urine_output = models.IntegerField(default=0, help_text="ml")
    drain_output = models.IntegerField(default=0, help_text="ml")
    emesis = models.IntegerField(default=0, help_text="ml")
    
    @property
    def net_balance(self):
        return (self.oral_intake + self.iv_intake) - (self.urine_output + self.drain_output + self.emesis)

class ShiftHandover(models.Model):
    outgoing_nurse = models.ForeignKey(User, on_delete=models.CASCADE, related_name='handovers_given')
    incoming_nurse = models.ForeignKey(User, on_delete=models.CASCADE, related_name='handovers_received')
    shift_date = models.DateField(default=timezone.now)
    shift_type = models.CharField(max_length=10, choices=[('day', 'Day Shift'), ('night', 'Night Shift')])
    
    patients = models.ManyToManyField(Patient, related_name='handovers')
    general_ward_notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Handover {self.shift_type} - {self.shift_date}"

class PatientAllergy(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=200)
    severity = models.CharField(max_length=20, choices=[('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe')], default='mild')
    reaction = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.allergen} ({self.severity})"

class ChronicCondition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='conditions')
    condition_name = models.CharField(max_length=255)
    diagnosed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('controlled', 'Controlled'), ('remission', 'Remission')], default='active')
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.condition_name
