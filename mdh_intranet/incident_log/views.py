from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Incident
from .forms import IncidentForm, IncidentUpdateForm


@login_required
def index(request):
    """Incident Log - list, filter, and search incidents."""
    incidents = Incident.objects.all()

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        incidents = incidents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(reported_by__username__icontains=search_query)
        )

    # Filters
    status_filter = request.GET.get('status', '')
    severity_filter = request.GET.get('severity', '')
    category_filter = request.GET.get('category', '')

    if status_filter:
        incidents = incidents.filter(status=status_filter)
    if severity_filter:
        incidents = incidents.filter(severity=severity_filter)
    if category_filter:
        incidents = incidents.filter(category=category_filter)

    # Stats (computed from ALL incidents, not filtered)
    all_incidents = Incident.objects.all()
    now = timezone.now()
    this_month = all_incidents.filter(
        date_reported__year=now.year,
        date_reported__month=now.month,
    )

    context = {
        'incidents': incidents.order_by('-date_reported'),
        'total_incidents': all_incidents.count(),
        'open_incidents': all_incidents.filter(status__in=['Open', 'Under Investigation']).count(),
        'resolved_incidents': all_incidents.filter(status__in=['Resolved', 'Closed']).count(),
        'this_month_count': this_month.count(),
        'critical_count': all_incidents.filter(severity='Critical', status__in=['Open', 'Under Investigation']).count(),
        # For filter dropdowns
        'search_query': search_query,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'category_filter': category_filter,
        'status_choices': Incident.STATUS_CHOICES,
        'severity_choices': Incident.SEVERITY_CHOICES,
        'category_choices': Incident.CATEGORY_CHOICES,
    }
    return render(request, 'incident_log/index.html', context)


@login_required
def create_incident(request):
    """Create a new incident report."""
    if request.method == 'POST':
        form = IncidentForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user
            incident.save()
            messages.success(request, f'Incident {incident.incident_number} reported successfully!')
            return redirect('incident_log:detail', pk=incident.pk)
    else:
        initial = {}
        patient_id = request.GET.get('patient_id')
        if patient_id:
            from mdh_intranet.clinical.models import Patient
            patient = get_object_or_404(Patient, pk=patient_id)
            initial = {
                'patient': patient.pk,
                'involved_type': 'PATIENT',
                'location': 'Clinical / Ward',
                'persons_involved': f"Patient: {patient.first_name} {patient.last_name} (#P{patient.id:05d})"
            }
        
        employee_id = request.GET.get('employee_id')
        if employee_id:
            from django.contrib.auth.models import User
            employee = get_object_or_404(User, pk=employee_id)
            initial = {
                'involved_employee': employee.pk,
                'involved_type': 'EMPLOYEE',
                'location': 'Office / Dept',
                'persons_involved': f"Staff: {employee.get_full_name() or employee.username}"
            }
        form = IncidentForm(initial=initial)

    return render(request, 'incident_log/create.html', {'form': form})


@login_required
def incident_detail(request, pk):
    """View a single incident's full details."""
    incident = get_object_or_404(Incident, pk=pk)

    context = {
        'incident': incident,
    }
    return render(request, 'incident_log/detail.html', context)


@login_required
def update_incident(request, pk):
    """Update incident status, resolution, etc. Staff only."""
    incident = get_object_or_404(Incident, pk=pk)

    # Only staff, the reporter, or assigned person can update
    if not (request.user.is_staff or request.user == incident.reported_by or request.user == incident.assigned_to):
        messages.error(request, 'You do not have permission to update this incident.')
        return redirect('incident_log:detail', pk=pk)

    if request.method == 'POST':
        form = IncidentUpdateForm(request.POST, request.FILES, instance=incident)
        if form.is_valid():
            updated_incident = form.save(commit=False)

            # Auto-set resolved_at and resolved_by when status changes to Resolved/Closed
            if updated_incident.status in ('Resolved', 'Closed') and not incident.resolved_at:
                updated_incident.resolved_at = timezone.now()
                updated_incident.resolved_by = request.user

            updated_incident.save()
            messages.success(request, f'Incident {incident.incident_number} updated successfully.')
            return redirect('incident_log:detail', pk=pk)
    else:
        form = IncidentUpdateForm(instance=incident)

    context = {
        'form': form,
        'incident': incident,
    }
    return render(request, 'incident_log/update.html', context)


@login_required
def delete_incident(request, pk):
    """Delete an incident. Staff/admin only."""
    incident = get_object_or_404(Incident, pk=pk)

    if not request.user.is_staff:
        messages.error(request, 'Only staff can delete incidents.')
        return redirect('incident_log:detail', pk=pk)

    if request.method == 'POST':
        number = incident.incident_number
        incident.delete()
        messages.success(request, f'Incident {number} has been deleted.')
        return redirect('incident_log:index')

    return render(request, 'incident_log/delete_confirm.html', {'incident': incident})
