"""
Core views: Audit Log, Notification Centre, Approval Workflows,
            Global Search, and Analytics Dashboard.
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    AuditLog, Notification, ApprovalWorkflow, ApprovalStep,
    SOPAcknowledgement, SOPReviewSchedule,
)
from .forms import ApprovalWorkflowForm
from .services import log_action, get_client_ip, notify

# Import models from other apps for search & analytics
from mdh_intranet.sop_manual.models import SOP
from mdh_intranet.documents.models import Document
from mdh_intranet.incident_log.models import Incident
from mdh_intranet.helpdesk.models import Ticket
from mdh_intranet.projects.models import Project
from mdh_intranet.leave_management.models import LeaveRequest
from mdh_intranet.capa.models import CAPARecord
from mdh_intranet.clinical.models import Patient, Consultation
from mdh_intranet.quality_audit.models import AuditSubmission, AuditTemplate

import csv
from django.http import HttpResponse


# ─── AUDIT LOG ──────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_log(request):
    """View the system-wide audit trail."""
    logs = AuditLog.objects.select_related('user', 'content_type').all()

    # Filters
    module = request.GET.get('module', '')
    action = request.GET.get('action', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if module:
        logs = logs.filter(module=module)
    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Aggregate stats for dashboard
    today = timezone.now().date()
    today_count = AuditLog.objects.filter(timestamp__date=today).count()
    total_count = AuditLog.objects.count()
    
    # Activity Trend (last 14 days)
    fourteen_days_ago = today - timedelta(days=13)
    trend_data = AuditLog.objects.filter(timestamp__date__gte=fourteen_days_ago)\
        .extra(select={'day': 'date(timestamp)'})\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')
    
    # Module Distribution
    module_stats = AuditLog.objects.values('module')\
        .annotate(count=Count('id'))\
        .order_by('-count')[:8]

    # Filters for UI
    modules = AuditLog.objects.values_list('module', flat=True).distinct()
    users = User.objects.filter(is_active=True).order_by('username')

    context = {
        'logs': logs[:200],
        'today_count': today_count,
        'total_count': total_count,
        'trend_json': json.dumps([{
            'day': str(d['day']), 
            'count': d['count']
        } for d in trend_data]),
        'module_json': json.dumps([{
            'module': m['module'] or 'System', 
            'count': m['count']
        } for m in module_stats]),
        'modules': sorted(set(m for m in modules if m)),
        'actions': AuditLog.ACTION_CHOICES,
        'users': users,
        'selected_module': module,
        'selected_action': action,
        'selected_user': user_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'core/audit_log.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_audit_csv(request):
    """Export the filtered audit trail to CSV."""
    logs = AuditLog.objects.select_related('user', 'content_type').all()
    
    # Apply same filters as the view
    module = request.GET.get('module', '')
    action = request.GET.get('action', '')
    if module: logs = logs.filter(module=module)
    if action: logs = logs.filter(action=action)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="MDH_Audit_Trail_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Action', 'Module', 'Object', 'Description', 'IP Address'])
    
    for log in logs[:1000]: # Limit export for performance
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'System',
            log.get_action_display(),
            log.module,
            log.object_repr,
            log.description,
            log.ip_address or '-'
        ])
    
    return response


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def compliance_hub(request):
    """Integrated hub for all compliance, auditing and quality activities."""
    # Quality Audits
    recent_inspections = AuditSubmission.objects.all().order_by('-conducted_at')[:5]
    total_inspections = AuditSubmission.objects.count()
    templates = AuditTemplate.objects.filter(is_active=True)
    
    # System Activity
    recent_logs = AuditLog.objects.exclude(action='login').order_by('-timestamp')[:10]
    raw_log_count = AuditLog.objects.count()
    
    # CAPAs
    open_capas = CAPARecord.objects.exclude(status__in=['closed', 'cancelled'])
    overdue_capas = open_capas.filter(target_completion_date__lt=timezone.now().date())
    
    # SOP Acknowledgements
    total_staff = User.objects.filter(is_active=True).count()
    acks = SOPAcknowledgement.objects.count()
    
    context = {
        'recent_inspections': recent_inspections,
        'templates': templates,
        'recent_logs': recent_logs,
        'open_capa_count': open_capas.count(),
        'overdue_capa_count': overdue_capas.count(),
        'ack_count': acks,
        'total_staff': total_staff,
        'total_inspections': total_inspections,
        'raw_log_count': raw_log_count,
    }
    return render(request, 'core/compliance_hub.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_detail(request, log_id):
    """View details of a single audit log entry."""
    entry = get_object_or_404(AuditLog, pk=log_id)
    context = {'entry': entry}
    return render(request, 'core/audit_detail.html', context)


# ─── NOTIFICATION CENTRE ───────────────────────────────────────

@login_required
def notification_list(request):
    """List all notifications for the current user."""
    notifications = Notification.objects.filter(recipient=request.user)

    filter_type = request.GET.get('type', '')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type:
        notifications = notifications.filter(notification_type=filter_type)

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    context = {
        'notifications': notifications[:100],
        'unread_count': unread_count,
        'filter_type': filter_type,
        'type_choices': Notification.TYPE_CHOICES,
    }
    return render(request, 'core/notifications.html', context)


@login_required
def notification_mark_read(request, notification_id):
    """Mark a single notification as read and redirect to its link."""
    notif = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    notif.mark_read()
    if notif.link:
        return redirect(notif.link)
    return redirect('core:notifications')


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read."""
    if request.method == 'POST':
        Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
    return redirect('core:notifications')


@login_required
def api_notifications(request):
    """AJAX endpoint for notification dropdown."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    data = {
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.pk,
                'title': n.title,
                'message': n.message[:100],
                'type': n.notification_type,
                'icon': n.type_icon,
                'color': n.type_color,
                'link': n.link,
                'is_read': n.is_read,
                'time_ago': _time_ago(n.created_at),
            }
            for n in notifications
        ],
    }
    return JsonResponse(data)


def _time_ago(dt):
    """Human-friendly time difference."""
    diff = timezone.now() - dt
    if diff.seconds < 60:
        return 'just now'
    elif diff.seconds < 3600:
        mins = diff.seconds // 60
        return f'{mins}m ago'
    elif diff.days == 0:
        hours = diff.seconds // 3600
        return f'{hours}h ago'
    elif diff.days == 1:
        return 'yesterday'
    elif diff.days < 7:
        return f'{diff.days}d ago'
    else:
        return dt.strftime('%b %d')


# ─── APPROVAL WORKFLOWS ────────────────────────────────────────

@login_required
def approval_list(request):
    """View pending approvals and recent workflow history."""
    # Items needing my approval
    pending_steps = ApprovalStep.objects.filter(
        approver=request.user, status='pending',
        workflow__status='pending',
    ).select_related('workflow', 'workflow__submitted_by').order_by('-workflow__submitted_at')

    # Check if current step matches
    pending_for_me = []
    for step in pending_steps:
        if step.order == step.workflow.current_step:
            pending_for_me.append(step)

    # My submitted workflows
    my_workflows = ApprovalWorkflow.objects.filter(
        submitted_by=request.user
    ).order_by('-updated_at')[:20]

    # All workflows (admin only)
    all_workflows = None
    if request.user.is_superuser:
        all_workflows = ApprovalWorkflow.objects.all().order_by('-updated_at')[:50]

    context = {
        'pending_for_me': pending_for_me,
        'my_workflows': my_workflows,
        'all_workflows': all_workflows,
    }
    return render(request, 'core/approvals.html', context)


@login_required
def approval_create(request):
    """Initiate a new multi-step approval workflow for any item."""
    if request.method == 'POST':
        form = ApprovalWorkflowForm(request.POST)
        if form.is_valid():
            # Create a 'virtual' object link if specific ID/CT not provided
            # (In this simple version, we mainly use object_repr and module)
            wf = form.save(commit=False)
            wf.submitted_by = request.user
            # We don't have a specific object_id/ct in this generic form, 
            # so we use a fallback to self for now.
            wf.content_type = ContentType.objects.get_for_model(ApprovalWorkflow)
            wf.object_id = 0 # Placeholder
            wf.save()

            # Process dynamic steps
            step_count = int(request.POST.get('step_count', 0))
            actual_steps = 0
            for i in range(1, step_count + 1):
                approver_id = request.POST.get(f'approver_{i}')
                role = request.POST.get(f'role_{i}', '')
                if approver_id:
                    approver = get_object_or_404(User, pk=approver_id)
                    ApprovalStep.objects.create(
                        workflow=wf,
                        order=actual_steps + 1,
                        approver=approver,
                        role_label=role
                    )
                    actual_steps += 1
            
            wf.total_steps = actual_steps
            wf.object_id = wf.id # Link to itself as the 'object'
            wf.save()

            if actual_steps > 0:
                wf.submit() # This starts the first notification
                log_action(request.user, 'submit', wf, 
                           description=f"Initiated approval for {wf.object_repr}",
                           ip_address=get_client_ip(request))
                messages.success(request, f'Approval workflow for "{wf.object_repr}" has been initiated!')
                return redirect('core:approvals')
            else:
                wf.delete()
                messages.error(request, 'You must add at least one approver step.')
    else:
        initial = {
            'object_repr': request.GET.get('object_repr', ''),
            'module': request.GET.get('module', ''),
        }
        form = ApprovalWorkflowForm(initial=initial)

    context = {
        'form': form,
        'users': User.objects.filter(is_active=True).order_by('username'),
    }
    return render(request, 'core/approval_form.html', context)


@login_required
def approval_detail(request, workflow_id):
    """View approval workflow details and act on pending steps."""
    workflow = get_object_or_404(ApprovalWorkflow, pk=workflow_id)
    steps = workflow.steps.select_related('approver').all()

    # Check if current user can act on current step
    can_act = False
    current_step_obj = None
    if workflow.status == 'pending':
        current_step_obj = steps.filter(order=workflow.current_step).first()
        if current_step_obj and current_step_obj.approver == request.user:
            can_act = True

    if request.method == 'POST' and can_act:
        action = request.POST.get('action', '')
        comments = request.POST.get('comments', '')

        if action == 'approve':
            current_step_obj.approve(comments)
            log_action(request.user, 'approve', workflow,
                       description=f'Approved step {current_step_obj.order}',
                       ip_address=get_client_ip(request))
            return redirect('core:approval_detail', workflow_id=workflow.pk)

        elif action == 'reject':
            current_step_obj.reject(comments)
            log_action(request.user, 'reject', workflow,
                       description=f'Rejected at step {current_step_obj.order}: {comments}',
                       ip_address=get_client_ip(request))
            return redirect('core:approval_detail', workflow_id=workflow.pk)

    # Audit trail for this workflow
    ct = workflow.content_type
    audit_entries = AuditLog.objects.filter(
        content_type=ct, object_id=workflow.object_id
    ).order_by('-timestamp')[:20]

    context = {
        'workflow': workflow,
        'steps': steps,
        'can_act': can_act,
        'current_step_obj': current_step_obj,
        'audit_entries': audit_entries,
    }
    return render(request, 'core/approval_detail.html', context)


# ─── GLOBAL SEARCH ──────────────────────────────────────────────

@login_required
def global_search(request):
    """Search across all modules."""
    query = request.GET.get('q', '').strip()
    results = {'sops': [], 'documents': [], 'incidents': [],
               'tickets': [], 'projects': [], 'capas': [], 'patients': []}
    total = 0

    if len(query) >= 2:
        # Clinical Patients
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) |
            Q(medical_aid_number__icontains=query) | Q(phone_number__icontains=query)
        )[:10]
        results['patients'] = patients
        total += patients.count()
        # SOPs
        sops = SOP.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )[:10]
        results['sops'] = sops
        total += sops.count()

        # Documents
        docs = Document.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10]
        results['documents'] = docs
        total += docs.count()

        # Incidents
        incidents = Incident.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10]
        results['incidents'] = incidents
        total += incidents.count()

        # Tickets
        tickets = Ticket.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10]
        results['tickets'] = tickets
        total += tickets.count()

        # Projects
        projects = Project.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]
        results['projects'] = projects
        total += projects.count()

        # CAPAs
        capas = CAPARecord.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) |
            Q(root_cause_summary__icontains=query)
        )[:10]
        results['capas'] = capas
        total += capas.count()

        # Log the search
        log_action(request.user, 'export', description=f'Searched: "{query}"',
                   module='search', ip_address=get_client_ip(request))

    context = {
        'query': query,
        'results': results,
        'total': total,
    }
    return render(request, 'core/search_results.html', context)


@login_required
def api_search(request):
    """AJAX endpoint for live search suggestions."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    suggestions = []

    # SOPs
    for sop in SOP.objects.filter(title__icontains=query)[:5]:
        suggestions.append({
            'title': sop.title,
            'type': 'SOP',
            'icon': 'fas fa-book',
            'url': f'/sops/{sop.pk}/',
        })

    # Documents
    for doc in Document.objects.filter(title__icontains=query)[:5]:
        suggestions.append({
            'title': doc.title,
            'type': 'Document',
            'icon': 'fas fa-file-alt',
            'url': f'/documents/',
        })

    # Patients
    for p in Patient.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))[:5]:
        suggestions.append({
            'title': f"Patient: {p}",
            'type': 'Clinical',
            'icon': 'fas fa-user-injured',
            'url': f'/clinical/patients/{p.pk}/',
        })

    return JsonResponse({'results': suggestions[:15]})


# ─── SOP ACKNOWLEDGEMENT ───────────────────────────────────────

@login_required
def sop_acknowledge(request, sop_id):
    """Staff acknowledges reading a specific SOP."""
    sop = get_object_or_404(SOP, pk=sop_id)

    if request.method == 'POST':
        ack, created = SOPAcknowledgement.objects.get_or_create(
            sop=sop,
            user=request.user,
            defaults={
                'ip_address': get_client_ip(request),
                'comments': request.POST.get('comments', ''),
            }
        )
        if created:
            log_action(request.user, 'acknowledge', sop,
                       description=f'Acknowledged SOP: {sop.title}',
                       ip_address=get_client_ip(request))
        return JsonResponse({
            'status': 'acknowledged',
            'timestamp': ack.acknowledged_at.isoformat(),
        })

    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def sop_acknowledgement_report(request):
    """Admin view: see which staff have acknowledged which SOPs."""
    sops = SOP.objects.annotate(
        ack_count=Count('acknowledgements'),
    ).order_by('-ack_count')

    total_staff = User.objects.filter(is_active=True).count()

    context = {
        'sops': sops,
        'total_staff': total_staff,
    }
    return render(request, 'core/acknowledgement_report.html', context)



