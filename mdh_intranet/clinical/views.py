from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import (
    Patient, Consultation, Prescription, PrescriptionItem, LabRequest, LabRequestItem, 
    ImagingRequest, ImagingItem, TheatreBooking, PatientVitals, PatientAllergy, ChronicCondition,
    Medication, DrugInteraction, NursingNote, FluidBalance, ShiftHandover
)
from .forms import (
    PatientForm, ConsultationForm, PrescriptionItemForm, LabRequestItemForm,
    ImagingItemForm, TheatreBookingForm, PatientVitalsForm, PatientAllergyForm, ChronicConditionForm,
    NursingNoteForm, FluidBalanceForm, ShiftHandoverForm
)
from mdh_intranet.core.services import log_action, notify, get_client_ip

@login_required 
def clinical_dashboard(request):
    """General Practitioner Dashboard."""
    recent_patients = Patient.objects.all().order_by('-created_at')[:5]
    recent_consultations = Consultation.objects.filter(gp=request.user).order_by('-date')[:5]
    
    # Stats
    total_patients = Patient.objects.all().count()
    today_consultations = Consultation.objects.filter(date__date=timezone.now().date()).count()
    pending_prescriptions = Prescription.objects.filter(status='pending').count()
    pending_lab = LabRequest.objects.exclude(status='completed').count()
    pending_imaging = ImagingRequest.objects.exclude(status='completed').count()
    scheduled_surgeries = TheatreBooking.objects.filter(proposed_date__date=timezone.now().date()).exclude(status='completed').count()
    
    return render(request, 'clinical/dashboard.html', {
        'recent_patients': recent_patients,
        'recent_consultations': recent_consultations,
        'total_patients': total_patients,
        'today_consultations': today_consultations,
        'pending_prescriptions': pending_prescriptions,
        'pending_lab': pending_lab,
        'pending_imaging': pending_imaging,
        'scheduled_surgeries': scheduled_surgeries,
    })

@login_required
def patient_list(request):
    """Searchable pagination list of patients."""
    query = request.GET.get('q', '')
    patient_list = Patient.objects.all().order_by('-created_at')
    
    if query:
        patient_list = patient_list.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(medical_aid_number__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(patient_list, 20) # 20 patients per page
    page = request.GET.get('page')
    try:
        patients = paginator.page(page)
    except PageNotAnInteger:
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages)
        
    return render(request, 'clinical/patient_list.html', {
        'patients': patients,
        'query': query,
    })

@login_required
def patient_create(request):
    """Add a new patient to the system."""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            log_action(request.user, 'create', patient, 
                       description=f"Created new patient: {patient}",
                       module='clinical', ip_address=get_client_ip(request))
            messages.success(request, f"Patient {patient} added successfully.")
            return redirect('clinical:patient_detail', pk=patient.pk)
    else:
        form = PatientForm()
    
    return render(request, 'clinical/patient_form.html', {'form': form, 'title': 'Add New Patient'})

@login_required
def patient_detail(request, pk):
    """View patient history and profile with vitals and allergies."""
    patient = get_object_or_404(Patient, pk=pk)
    consultations = patient.consultations.all().order_by('-date')
    latest_vitals = patient.vitals.first()
    allergies = patient.allergies.all()
    conditions = patient.conditions.all()
    
    return render(request, 'clinical/patient_detail.html', {
        'patient': patient,
        'consultations': consultations,
        'nursing_notes': patient.nursing_notes.all().order_by('-recorded_at'),
        'latest_vitals': latest_vitals,
        'allergies': allergies,
        'conditions': conditions,
    })

@login_required
def log_vitals(request, patient_pk):
    """Triage view: log patient vitals."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        form = PatientVitalsForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.patient = patient
            vitals.recorded_by = request.user
            vitals.save()
            log_action(request.user, 'triage', patient, 
                       description=f"Logged vitals for {patient}",
                       module='clinical', ip_address=get_client_ip(request))
            messages.success(request, "Vital signs recorded.")
            return redirect('clinical:patient_detail', pk=patient.pk)
    else:
        form = PatientVitalsForm()
    
    return render(request, 'clinical/log_vitals.html', {
        'patient': patient,
        'form': form
    })

@login_required
def manage_allergies(request, patient_pk):
    """View and add patient allergies."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        form = PatientAllergyForm(request.POST)
        if form.is_valid():
            allergy = form.save(commit=False)
            allergy.patient = patient
            allergy.save()
            messages.success(request, f"Added allergy: {allergy}")
            return redirect('clinical:patient_detail', pk=patient.pk)
    
    return redirect('clinical:patient_detail', pk=patient.pk)

@login_required
def check_drug_interactions(request):
    """AJAX view to check for drug-drug interactions."""
    med_ids = request.GET.getlist('med_ids[]')
    patient_id = request.GET.get('patient_id')
    
    if not med_ids:
        return JsonResponse({'interactions': []})
    
    medications = Medication.objects.filter(id__in=med_ids)
    warnings = []
    
    # Check interactions among the new group of drugs
    for i, med_a in enumerate(medications):
        for med_b in medications[i+1:]:
            interaction = DrugInteraction.objects.filter(
                (Q(drug_a=med_a, drug_b=med_b) | Q(drug_a=med_b, drug_b=med_a))
            ).first()
            if interaction:
                warnings.append({
                    'drug_a': med_a.name,
                    'drug_b': med_b.name,
                    'severity': interaction.severity,
                    'message': interaction.warning_message
                })
    
    # Check against patient's active prescriptions (last 30 days)
    if patient_id:
        active_rx_items = PrescriptionItem.objects.filter(
            prescription__consultation__patient_id=patient_id,
            prescription__status='dispensed',
            prescription__created_at__gte=timezone.now() - timezone.timedelta(days=30),
            medication__isnull=False
        ).select_related('medication')
        
        active_meds = {item.medication for item in active_rx_items}
        
        for med_new in medications:
            for med_active in active_meds:
                if med_new == med_active: continue
                interaction = DrugInteraction.objects.filter(
                    (Q(drug_a=med_new, drug_b=med_active) | Q(drug_a=med_active, drug_b=med_new))
                ).first()
                if interaction:
                    warnings.append({
                        'drug_a': med_new.name,
                        'drug_b': med_active.name,
                        'severity': interaction.severity,
                        'message': f"CURRENT MEDICATION OVERLAP: {interaction.warning_message}"
                    })

        # 3. Check for Patient Allergies
        patient = get_object_or_404(Patient, id=patient_id)
        allergies = patient.allergies.all()
        for med in medications:
            for allergy in allergies:
                # Match against Name, Generic Name, or Drug Class (e.g. 'Penicillin')
                search_targets = [med.name.lower(), med.generic_name.lower()]
                if med.drug_class:
                    search_targets.append(med.drug_class.lower())
                
                allergen_clean = allergy.allergen.lower().strip()
                if any(allergen_clean in target for target in search_targets):
                    warnings.append({
                        'drug_a': med.name,
                        'drug_b': '🚨 ALLERGY MATCH',
                        'severity': 'major',
                        'message': f"PATIENT ALLERGY: Contraindicated due to {allergy.allergen} allergy. Reaction: {allergy.reaction or 'Noted'}."
                    })

    return JsonResponse({'interactions': warnings})

@login_required
def consultation_create(request, patient_id):
    """Record a GP consultation, write prescriptions, and order tests."""
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.gp = request.user
            consultation.save()
            
            # 1. Process Prescriptions if medications provided
            meds = request.POST.getlist('med_name[]')
            if meds and meds[0]:
                prescription = Prescription.objects.create(
                    consultation=consultation,
                    prescribed_by=request.user
                )
                ids = request.POST.getlist('med_id[]')
                for i in range(len(meds)):
                    if meds[i]:
                        med_id = ids[i] if i < len(ids) and ids[i] else None
                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medication_id=med_id,
                            medication_name=meds[i],
                            dosage=request.POST.getlist('med_dosage[]')[i],
                            frequency=request.POST.getlist('med_freq[]')[i],
                            duration=request.POST.getlist('med_duration[]')[i],
                            total_quantity=request.POST.getlist('med_qty[]')[i],
                            instructions=request.POST.getlist('med_inst[]')[i] or ""
                        )
                
                # Notify Pharmacy Group
                # Assume group of pharmacists exist or notify admins for now
                pharmacy_users = User.objects.filter(groups__name='Pharmacy')
                if not pharmacy_users.exists():
                    # Fallback to notify all admins if no pharmacy group
                    pharmacy_users = User.objects.filter(is_superuser=True)
                
                for phu in pharmacy_users:
                    notify(phu, f"New Prescription: {patient}", 'system', 
                           message=f"New prescription request from Dr. {request.user.get_full_name()} for {patient}",
                           link=f"/clinical/pharmacy/", 
                           priority='high', icon='fas fa-pills')

            # 2. Process Lab Requests if tests provided
            tests = request.POST.getlist('test_name[]')
            if tests and tests[0]:
                lab_req = LabRequest.objects.create(
                    consultation=consultation,
                    gp=request.user,
                    urgency=request.POST.get('lab_urgency', 'normal')
                )
                for i in range(len(tests)):
                    if tests[i]:
                        LabRequestItem.objects.create(
                            lab_request=lab_req,
                            test_name=tests[i],
                            specimen_type=request.POST.getlist('specimen[]')[i] or ""
                        )
                
                # Notify Lab Group
                lab_users = User.objects.filter(groups__name='Laboratory') or User.objects.filter(is_superuser=True)
                for lu in lab_users:
                    notify(lu, f"Lab Request Ordered: {patient}", 'system',
                           message=f"Test order from Dr. {request.user.get_full_name()} for {patient}",
                           link=f"/clinical/lab/", priority='normal', icon='fas fa-flask')

            # 3. Process Imaging Requests if provided
            imaging_modalities = request.POST.getlist('img_modality[]')
            if imaging_modalities and imaging_modalities[0]:
                img_req = ImagingRequest.objects.create(
                    consultation=consultation,
                    gp=request.user,
                    urgency=request.POST.get('img_urgency', 'normal')
                )
                areas = request.POST.getlist('img_area[]')
                questions = request.POST.getlist('img_question[]')
                for i in range(len(imaging_modalities)):
                    if imaging_modalities[i]:
                        ImagingItem.objects.create(
                            imaging_request=img_req,
                            modality=imaging_modalities[i],
                            view_area=areas[i] if i < len(areas) else "",
                            clinical_question=questions[i] if i < len(questions) else ""
                        )
                
                # Notify Radiology Group
                img_users = User.objects.filter(groups__name='Imaging') or User.objects.filter(is_superuser=True)
                for iu in img_users:
                    notify(iu, f"Imaging Ordered: {patient}", 'system',
                           message=f"New scan request from Dr. {request.user.get_full_name()} for {patient}",
                           link=f"/clinical/imaging/", priority='high', icon='fas fa-x-ray')

            # 4. Process Theatre Booking if provided
            procedure = request.POST.get('theatre_procedure')
            if procedure:
                TheatreBooking.objects.create(
                    consultation=consultation,
                    patient=patient,
                    procedure_name=procedure,
                    priority=request.POST.get('theatre_priority', 'elective'),
                    proposed_date=request.POST.get('theatre_date'),
                    estimated_duration=request.POST.get('theatre_duration', 60),
                    surgeon=request.user,
                    assistant_surgeon=request.POST.get('theatre_assistant', ''),
                    anaesthetist=request.POST.get('theatre_anaesthetist', ''),
                    theatre_notes=request.POST.get('theatre_notes', '')
                )
                
                # Notify Theatre Group
                th_users = User.objects.filter(groups__name='Theatre') or User.objects.filter(is_superuser=True)
                for tu in th_users:
                    notify(tu, f"New Theatre Booking: {patient}", 'system',
                           message=f"Surgery scheduled for {patient} - {procedure}",
                           link=f"/clinical/theatre/", priority='high', icon='fas fa-procedures')

            log_action(request.user, 'create', consultation, 
                       description=f"Consultation for {patient}",
                       module='clinical', ip_address=get_client_ip(request))
            
            messages.success(request, f"Consultation for {patient} recorded.")
            return redirect('clinical:consultation_detail', pk=consultation.pk)
    else:
        form = ConsultationForm()
    
    return render(request, 'clinical/consultation_form.html', {
        'form': form,
        'patient': patient,
        'title': f'Consultation: {patient}',
        'medications': Medication.objects.all().order_by('name')
    })

@login_required
def my_consultations(request):
    """List of consultations by the current GP."""
    consultations = Consultation.objects.filter(gp=request.user).order_by('-date')
    return render(request, 'clinical/consultation_list.html', {
        'consultations': consultations,
        'title': 'My Clinical Encounters'
    })

@login_required
def consultation_history(request):
    """Full departmental clinical history (All Doctors)."""
    consultations = Consultation.objects.all().order_by('-date')
    return render(request, 'clinical/consultation_list.html', {
        'consultations': consultations,
        'title': 'All Clinical History'
    })

@login_required
def consultation_detail(request, pk):
    """View consultation summary."""
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'clinical/consultation_detail.html', {'consultation': consultation})

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Pharmacy').exists() or u.is_staff)
def pharmacy_dashboard(request):
    """Worklist for pharmacy to view and dispense prescriptions."""
    prescriptions = Prescription.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'clinical/pharmacy_dashboard.html', {'prescriptions': prescriptions})

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Laboratory').exists() or u.is_staff)
def lab_dashboard(request):
    """Worklist for laboratory."""
    requests = LabRequest.objects.exclude(status='completed').order_by('-created_at')
    return render(request, 'clinical/lab_dashboard.html', {'lab_requests': requests})

@login_required
def prescription_detail(request, pk):
    """View prescription details."""
    prescription = get_object_or_404(Prescription, pk=pk)
    return render(request, 'clinical/prescription_detail.html', {'prescription': prescription})

@login_required
def dispense_prescription(request, pk):
    """Mark a prescription as dispensed by pharmacist."""
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        prescription.status = 'dispensed'
        prescription.dispensed_by = request.user
        prescription.dispensed_at = timezone.now()
        prescription.pharmacy_notes = request.POST.get('notes', '')
        prescription.save()
        
        # Notify GP
        notify(prescription.prescribed_by, f"Prescription Dispensed: {prescription.consultation.patient}", 'system',
               message=f"Pharmacist {request.user.get_full_name()} has dispensed the medication.",
               link=f"/clinical/prescriptions/{prescription.pk}/", priority='low', icon='fas fa-pills')
        
        messages.success(request, "Prescription marked as dispensed.")
        return redirect('clinical:pharmacy_dashboard')
    
    return redirect('clinical:prescription_detail', pk=pk)

@login_required
def lab_request_detail(request, pk):
    """View lab request details and results."""
    lab_req = get_object_or_404(LabRequest, pk=pk)
    return render(request, 'clinical/lab_request_detail.html', {'lab_req': lab_req})

@login_required
def update_lab_status(request, pk):
    """Update status of lab request (for lab technicians)."""
    lab_req = get_object_or_404(LabRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = lab_req.get_status_display()
        lab_req.status = new_status
        
        if new_status == 'completed':
            lab_req.results_ready = True
            lab_req.results_url = request.POST.get('results_url', '')
            # Notify GP
            notify(lab_req.gp, f"Lab Results Ready: {lab_req.consultation.patient}", 'system',
                   message=f"Results for tests ordered on {lab_req.created_at.date()} are now available.",
                   link=f"/clinical/lab/{lab_req.pk}/", priority='high', icon='fas fa-file-medical')
        
        lab_req.save()
        messages.success(request, f"Lab status updated to: {lab_req.get_status_display()}")
        
    return redirect('clinical:lab_dashboard')

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Imaging').exists() or u.is_staff)
def imaging_dashboard(request):
    """Radiology worklist."""
    requests = ImagingRequest.objects.exclude(status='completed').order_by('-created_at')
    return render(request, 'clinical/imaging_dashboard.html', {'imaging_requests': requests})

@login_required
def imaging_request_detail(request, pk):
    """Radiology request detail and upload results."""
    img_req = get_object_or_404(ImagingRequest, pk=pk)
    return render(request, 'clinical/imaging_request_detail.html', {'img_req': img_req})

@login_required
def update_imaging_status(request, pk):
    """Update status of imaging request."""
    img_req = get_object_or_404(ImagingRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        img_req.status = new_status
        if new_status == 'completed':
            img_req.report_ready = True
            img_req.results_url = request.POST.get('results_url', img_req.results_url)
            if 'report_file' in request.FILES:
                img_req.report_file = request.FILES['report_file']
            
            # Notify GP
            notify(img_req.gp, f"Imaging Report Ready: {img_req.consultation.patient}", 'system',
                   message=f"Radiology results for {img_req.consultation.patient} are now available.",
                   link=f"/clinical/imaging/{img_req.pk}/", priority='high', icon='fas fa-file-image')
        img_req.save()
        messages.success(request, f"Imaging status updated to: {img_req.get_status_display()}")
    return redirect('clinical:imaging_dashboard')

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Theatre').exists() or u.is_staff)
def theatre_dashboard(request):
    """Scheduled surgeries worklist."""
    bookings = TheatreBooking.objects.exclude(status='completed').order_by('proposed_date')
    return render(request, 'clinical/theatre_dashboard.html', {'bookings': bookings})

@login_required
def theatre_booking_detail(request, pk):
    """Update surgery status."""
    booking = get_object_or_404(TheatreBooking, pk=pk)
    return render(request, 'clinical/theatre_booking_detail.html', {'booking': booking})

@login_required
def update_theatre_status(request, pk):
    """Update theatre booking status."""
    booking = get_object_or_404(TheatreBooking, pk=pk)
    if request.method == 'POST':
        booking.status = request.POST.get('status')
        booking.theatre_number = request.POST.get('theatre_number', booking.theatre_number)
        booking.save()
        messages.success(request, f"Theatre status updated to: {booking.get_status_display()}")
    return redirect('clinical:theatre_dashboard')

# PDF Downloads
@login_required
def download_consultation_pdf(request, pk):
    """Generate PDF for Consultation Notes."""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    consultation = get_object_or_404(Consultation, pk=pk)
    
    html_content = render_to_string('clinical/consultation_pdf.html', {
        'consultation': consultation,
        'generated_at': timezone.now(),
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"Consultation_{consultation.pk}_{consultation.patient.last_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def download_prescription_pdf(request, pk):
    """Generate PDF for Prescription."""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    prescription = get_object_or_404(Prescription, pk=pk)
    
    html_content = render_to_string('clinical/prescription_pdf.html', {
        'prescription': prescription,
        'generated_at': timezone.now(),
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"Prescription_{prescription.pk}_{prescription.consultation.patient.last_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def download_lab_request_pdf(request, pk):
    """Generate PDF for Lab request form."""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    lab_req = get_object_or_404(LabRequest, pk=pk)
    
    html_content = render_to_string('clinical/lab_request_pdf.html', {
        'lab_req': lab_req,
        'generated_at': timezone.now(),
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"LabRequest_{lab_req.pk}_{lab_req.consultation.patient.last_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['Nursing', 'Clinical']).exists() or u.is_superuser)
def nursing_dashboard(request):
    """Dashboard for nursing staff to manage ward activities."""
    current_handovers = ShiftHandover.objects.filter(is_completed=False).order_by('-created_at')
    recent_notes = NursingNote.objects.all().order_by('-recorded_at')[:10]
    
    # Ward view: patients with consultations in the last 7 days (broadened for visibility)
    ward_patients = Patient.objects.filter(
        consultations__date__gte=timezone.now() - timezone.timedelta(days=7)
    ).distinct()
    
    return render(request, 'clinical/nursing_dashboard.html', {
        'handovers': current_handovers,
        'recent_notes': recent_notes,
        'ward_patients': ward_patients,
    })

@login_required
def log_nursing_note(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = NursingNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.patient = patient
            note.nurse = request.user
            note.save()
            messages.success(request, f"Nursing note recorded for {patient}")
            return redirect('clinical:patient_detail', pk=patient.pk)
    else:
        form = NursingNoteForm()
    
    # Context for better clinical decision making
    latest_vitals = patient.vitals.first()
    previous_notes = patient.nursing_notes.all().order_by('-recorded_at')[:5]
    
    return render(request, 'clinical/log_nursing_note.html', {
        'form': form, 
        'patient': patient,
        'latest_vitals': latest_vitals,
        'previous_notes': previous_notes,
    })

@login_required
def log_fluid_balance(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = FluidBalanceForm(request.POST)
        if form.is_valid():
            balance = form.save(commit=False)
            balance.patient = patient
            balance.recorded_by = request.user
            balance.save()
            messages.success(request, f"Fluid balance recorded for {patient}")
            return redirect('clinical:patient_detail', pk=patient.pk)
    else:
        form = FluidBalanceForm()
    
    return render(request, 'clinical/log_fluid_balance.html', {'form': form, 'patient': patient})

@login_required
def handover_create(request):
    if request.method == 'POST':
        form = ShiftHandoverForm(request.POST)
        if form.is_valid():
            handover = form.save(commit=False)
            handover.outgoing_nurse = request.user
            handover.save()
            form.save_m2m() # For patients ManyToMany
            messages.success(request, "Shift handover registered successfully.")
            return redirect('clinical:nursing_dashboard')
    else:
        form = ShiftHandoverForm()
    
    return render(request, 'clinical/handover_form.html', {'form': form})

@login_required
def handover_detail(request, pk):
    handover = get_object_or_404(ShiftHandover, pk=pk)
    return render(request, 'clinical/handover_detail.html', {'handover': handover})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def clinical_manager_dashboard(request):
    """Unified management view for all clinical activities."""
    pending_prescriptions = Prescription.objects.filter(status='pending').count()
    active_theatre = TheatreBooking.objects.filter(status='in-theatre').count()
    pending_theatre = TheatreBooking.objects.filter(status__in=['scheduled', 'pre-op']).count()
    pending_lab = LabRequest.objects.filter(status='requested').count()
    pending_imaging = ImagingRequest.objects.filter(status='requested').count()
    
    recent_emergency_vitals = PatientVitals.objects.filter(
        level_of_consciousness__in=['P', 'U']
    ).order_by('-recorded_at')[:5]
    
    # Theatre Room Occupancy
    rooms = TheatreBooking.objects.filter(status='in-theatre').values('theatre_number', 'patient__last_name', 'procedure_name')
    
    return render(request, 'clinical/manager_dashboard.html', {
        'pending_rx': pending_prescriptions,
        'active_theatre': active_theatre,
        'pending_theatre': pending_theatre,
        'pending_lab': pending_lab,
        'pending_img': pending_imaging,
        'emergency_patients': recent_emergency_vitals,
        'theatre_rooms': rooms,
    })
