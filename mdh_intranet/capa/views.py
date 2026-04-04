"""
CAPA views: list, create, detail, update phases, advance status, add comments.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import CAPARecord, CAPAComment
from .forms import (
    CAPACreateForm, CAPAInvestigationForm, CAPAActionPlanForm,
    CAPAVerificationForm, CAPACommentForm,
)
from mdh_intranet.core.services import log_action, notify, get_client_ip


@login_required
def capa_list(request):
    """Dashboard view listing all CAPA records with filters and stats."""
    records = CAPARecord.objects.select_related(
        'initiated_by', 'assigned_to', 'linked_incident'
    ).all()

    # Filters
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    capa_type = request.GET.get('type', '')
    search = request.GET.get('q', '').strip()
    view_mode = request.GET.get('view', 'all')

    if status:
        records = records.filter(status=status)
    if priority:
        records = records.filter(priority=priority)
    if capa_type:
        records = records.filter(capa_type=capa_type)
    if search:
        records = records.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(root_cause_summary__icontains=search)
        )
    if view_mode == 'mine':
        records = records.filter(
            Q(assigned_to=request.user) | Q(initiated_by=request.user)
        )
    elif view_mode == 'overdue':
        records = records.filter(
            target_completion_date__lt=timezone.now().date()
        ).exclude(status__in=['closed', 'cancelled'])

    # Stats
    total = CAPARecord.objects.count()
    open_count = CAPARecord.objects.exclude(
        status__in=['closed', 'cancelled']
    ).count()
    overdue_count = CAPARecord.objects.filter(
        target_completion_date__lt=timezone.now().date()
    ).exclude(status__in=['closed', 'cancelled']).count()
    closed_this_month = CAPARecord.objects.filter(
        status='closed',
        closed_at__month=timezone.now().month,
        closed_at__year=timezone.now().year,
    ).count()

    # Status distribution for mini chart
    status_counts = dict(
        CAPARecord.objects.values_list('status')
        .annotate(c=Count('id'))
        .values_list('status', 'c')
    )

    context = {
        'records': records[:100],
        'total': total,
        'open_count': open_count,
        'overdue_count': overdue_count,
        'closed_this_month': closed_this_month,
        'status_counts': status_counts,
        'selected_status': status,
        'selected_priority': priority,
        'selected_type': capa_type,
        'search_query': search,
        'view_mode': view_mode,
        'status_choices': CAPARecord.STATUS_CHOICES,
        'priority_choices': CAPARecord.PRIORITY_CHOICES,
        'type_choices': CAPARecord.TYPE_CHOICES,
    }
    return render(request, 'capa/capa_list.html', context)


@login_required
def capa_create(request):
    """Create a new CAPA record."""
    if request.method == 'POST':
        form = CAPACreateForm(request.POST, request.FILES)
        if form.is_valid():
            capa = form.save(commit=False)
            capa.initiated_by = request.user
            capa.status = 'draft'
            capa.save()

            log_action(request.user, 'create', capa,
                       description=f'Created CAPA: {capa.title}',
                       ip_address=get_client_ip(request))

            # Notify assigned person
            if capa.assigned_to and capa.assigned_to != request.user:
                notify(
                    capa.assigned_to,
                    f'New CAPA assigned: {capa.capa_number}',
                    notification_type='system',
                    message=f'{request.user.get_full_name() or request.user.username} assigned you CAPA: {capa.title}',
                    link=f'/capa/{capa.pk}/',
                    priority='high',
                    icon='fas fa-exclamation-circle',
                    send_email=True,
                )

            messages.success(request, f'{capa.capa_number} created successfully.')
            return redirect('capa:detail', pk=capa.pk)
    else:
        # Pre-fill from incident or audit if provided
        initial = {}
        incident_id = request.GET.get('incident')
        audit_id = request.GET.get('audit')

        if incident_id:
            from mdh_intranet.incident_log.models import Incident
            try:
                incident = Incident.objects.get(pk=incident_id)
                initial = {
                    'linked_incident': incident,
                    'title': f'CAPA for {incident.incident_number}: {incident.title}',
                    'description': f'Originating incident: {incident.description}',
                    'source': 'incident',
                }
                if incident.severity in ('High', 'Critical'):
                    initial['priority'] = incident.severity.lower()
            except Incident.DoesNotExist:
                pass

        elif audit_id:
            from mdh_intranet.quality_audit.models import AuditSubmission
            try:
                submission = AuditSubmission.objects.get(pk=audit_id)
                failures = submission.answers.filter(passed=False)
                failure_text = "\n".join([f"- {f.question.text}: {f.comments}" for f in failures])
                
                initial = {
                    'title': f'CAPA for Audit: {submission.template.title} ({submission.department_audited})',
                    'description': f'Quality audit findings for {submission.department_audited} on {submission.conducted_at.date()}.\n\nFailures recorded:\n{failure_text}',
                    'source': 'audit',
                }
                if failures.count() > 3:
                    initial['priority'] = 'high'
            except AuditSubmission.DoesNotExist:
                pass

        form = CAPACreateForm(initial=initial)

    context = {
        'form': form,
        'users': User.objects.filter(is_active=True).order_by('username'),
    }
    return render(request, 'capa/capa_create.html', context)


@login_required
def capa_detail(request, pk):
    """View CAPA details with full timeline and phase-specific forms."""
    capa = get_object_or_404(
        CAPARecord.objects.select_related(
            'initiated_by', 'assigned_to', 'verified_by',
            'closed_by', 'linked_incident'
        ),
        pk=pk
    )
    comments = capa.comments.select_related('author').all()
    comment_form = CAPACommentForm()

    # Phase-specific forms
    investigation_form = CAPAInvestigationForm(instance=capa)
    action_plan_form = CAPAActionPlanForm(instance=capa)
    verification_form = CAPAVerificationForm(instance=capa)

    context = {
        'capa': capa,
        'comments': comments,
        'comment_form': comment_form,
        'investigation_form': investigation_form,
        'action_plan_form': action_plan_form,
        'verification_form': verification_form,
    }
    return render(request, 'capa/capa_detail.html', context)


@login_required
def capa_update_phase(request, pk, phase):
    """Update a specific phase of the CAPA record."""
    capa = get_object_or_404(CAPARecord, pk=pk)

    form_map = {
        'investigation': CAPAInvestigationForm,
        'action_plan': CAPAActionPlanForm,
        'verification': CAPAVerificationForm,
    }

    FormClass = form_map.get(phase)
    if not FormClass:
        messages.error(request, 'Invalid phase.')
        return redirect('capa:detail', pk=pk)

    if request.method == 'POST':
        form = FormClass(request.POST, instance=capa)
        if form.is_valid():
            capa = form.save()

            # Update verification metadata
            if phase == 'verification':
                capa.verification_date = timezone.now().date()
                capa.verified_by = request.user
                capa.save()

            log_action(request.user, 'update', capa,
                       description=f'Updated {phase} phase for {capa.capa_number}',
                       ip_address=get_client_ip(request))

            messages.success(request, f'{phase.replace("_", " ").title()} updated.')
            return redirect('capa:detail', pk=pk)

    messages.error(request, 'Invalid request.')
    return redirect('capa:detail', pk=pk)


@login_required
def capa_advance(request, pk):
    """Advance the CAPA to the next status in the workflow."""
    capa = get_object_or_404(CAPARecord, pk=pk)

    if request.method == 'POST':
        old_status = capa.get_status_display()
        if capa.advance_status():
            new_status = capa.get_status_display()

            log_action(request.user, 'update', capa,
                       changes={'status': {'old': old_status, 'new': new_status}},
                       description=f'Advanced {capa.capa_number} to {new_status}',
                       ip_address=get_client_ip(request))

            # Notify assigned person
            if capa.assigned_to and capa.assigned_to != request.user:
                notify(
                    capa.assigned_to,
                    f'{capa.capa_number} advanced to {new_status}',
                    notification_type='system',
                    message=f'{request.user.get_full_name() or request.user.username} advanced this CAPA.',
                    link=f'/capa/{capa.pk}/',
                    icon='fas fa-arrow-right',
                    send_email=True,
                )

            if capa.status == 'closed':
                capa.closed_by = request.user
                capa.actual_completion_date = timezone.now().date()
                capa.save()
                messages.success(request, f'{capa.capa_number} has been closed.')
            else:
                messages.success(request, f'Advanced to: {new_status}')
        else:
            messages.warning(request, 'Cannot advance further.')

    return redirect('capa:detail', pk=pk)


@login_required
def capa_add_comment(request, pk):
    """Add a timeline comment to a CAPA record."""
    capa = get_object_or_404(CAPARecord, pk=pk)

    if request.method == 'POST':
        form = CAPACommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.capa = capa
            comment.author = request.user
            comment.save()

            log_action(request.user, 'update', capa,
                       description=f'Added comment on {capa.capa_number}',
                       ip_address=get_client_ip(request))

            messages.success(request, 'Comment added.')

    return redirect('capa:detail', pk=pk)
