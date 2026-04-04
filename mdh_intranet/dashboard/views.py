from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from mdh_intranet.documents.models import Document
from mdh_intranet.sop_manual.models import SOP
from mdh_intranet.incident_log.models import Incident
from mdh_intranet.projects.models import Project
from mdh_intranet.dashboard.models import Announcement
from mdh_intranet.medical_aid.models import PreauthorizationRequest
from mdh_intranet.helpdesk.models import Ticket
from mdh_intranet.leave_management.models import LeaveRequest
from mdh_intranet.capa.models import CAPARecord


@login_required
def index(request):
    """Executive Dashboard - requires authentication."""

    # Fetch stats
    incident_count = Incident.objects.filter(status='Open').count()
    ticket_count = Ticket.objects.filter(requester=request.user, status='open').count()
    doc_count = Document.objects.count()
    sop_count = SOP.objects.count()
    project_count = Project.objects.filter(status='Active').count()

    # Fetch functional data
    announcements = Announcement.objects.filter(is_active=True)[:5]
    staff_members = User.objects.filter(is_active=True).select_related('profile').order_by('last_name')[:8]
    medical_requests = PreauthorizationRequest.objects.all().order_by('-created_at')[:5]

    context = {
        'page_title': 'Executive Dashboard',
        'user_name': request.user.get_full_name() or request.user.username,
        'incident_count': incident_count,
        'ticket_count': ticket_count,
        'doc_count': doc_count,
        'sop_count': sop_count,
        'project_count': project_count,
        'announcements': announcements,
        'staff_members': staff_members,
        'medical_requests': medical_requests,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def schedule(request):
    """Schedule page - shows upcoming leave, SOP reviews, CAPA deadlines, and project milestones."""
    today = timezone.now().date()
    next_30 = today + timedelta(days=30)
    next_90 = today + timedelta(days=90)

    # Upcoming leave (user's own)
    my_leave = LeaveRequest.objects.filter(
        user=request.user,
        status__in=['PENDING', 'APPROVED'],
        end_date__gte=today,
    ).order_by('start_date')[:10]

    # Team leave (if staff/admin)
    team_leave = []
    if request.user.is_staff:
        team_leave = LeaveRequest.objects.filter(
            status='APPROVED',
            end_date__gte=today,
        ).exclude(user=request.user).select_related('user', 'leave_type').order_by('start_date')[:10]

    # SOP Review Schedule (from core)
    from mdh_intranet.core.models import SOPReviewSchedule
    sop_reviews = SOPReviewSchedule.objects.filter(
        next_review_at__isnull=False,
        next_review_at__date__lte=next_90,
    ).select_related('sop', 'reviewer').order_by('next_review_at')[:10]

    overdue_reviews = SOPReviewSchedule.objects.filter(
        next_review_at__isnull=False,
        next_review_at__date__lt=today,
    ).select_related('sop', 'reviewer').order_by('next_review_at')

    # CAPA deadlines
    capa_deadlines = CAPARecord.objects.filter(
        target_completion_date__isnull=False,
        target_completion_date__gte=today,
        target_completion_date__lte=next_90,
        status__in=['open', 'in_progress'],
    ).order_by('target_completion_date')[:10]

    overdue_capas = CAPARecord.objects.filter(
        target_completion_date__isnull=False,
        target_completion_date__lt=today,
        status__in=['open', 'in_progress'],
    ).order_by('target_completion_date')

    # Active projects
    active_projects = Project.objects.filter(
        status='Active',
    ).order_by('end_date')[:5]

    # Build timeline events for a unified view
    timeline_events = []

    for leave in my_leave:
        timeline_events.append({
            'date': leave.start_date,
            'end_date': leave.end_date,
            'title': f'{leave.leave_type.name if leave.leave_type else "Leave"}',
            'subtitle': f'{leave.get_status_display()}',
            'icon': 'fas fa-plane-departure',
            'color': 'success' if leave.status == 'APPROVED' else 'warning',
            'category': 'leave',
        })

    for review in sop_reviews:
        is_overdue = review.next_review_at and review.next_review_at.date() < today
        timeline_events.append({
            'date': review.next_review_at.date() if review.next_review_at else today,
            'title': f'SOP Review: {review.sop.title[:40]}',
            'subtitle': f'Reviewer: {review.reviewer.get_full_name() if review.reviewer else "Unassigned"}',
            'icon': 'fas fa-book',
            'color': 'danger' if is_overdue else 'info',
            'category': 'sop_review',
        })

    for capa in capa_deadlines:
        timeline_events.append({
            'date': capa.target_completion_date,
            'title': f'CAPA: {capa.title[:40]}',
            'subtitle': f'{capa.get_status_display()} · {capa.get_priority_display()}',
            'icon': 'fas fa-clipboard-check',
            'color': 'primary',
            'category': 'capa',
        })

    # Sort timeline by date
    timeline_events.sort(key=lambda x: x['date'])

    context = {
        'page_title': 'Schedule',
        'today': today,
        'my_leave': my_leave,
        'team_leave': team_leave,
        'sop_reviews': sop_reviews,
        'overdue_reviews': overdue_reviews,
        'capa_deadlines': capa_deadlines,
        'overdue_capas': overdue_capas,
        'active_projects': active_projects,
        'timeline_events': timeline_events,
    }
    return render(request, 'dashboard/schedule.html', context)


@login_required
def settings_view(request):
    """User settings page - profile info, preferences."""
    user = request.user

    # Ensure profile exists
    try:
        profile = user.profile
    except Exception:
        from mdh_intranet.user_management.models import UserProfile
        profile = UserProfile.objects.create(user=user)

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            # Update user info
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.save()

            # Update profile info
            profile.department = request.POST.get('department', '').strip()
            profile.role = request.POST.get('role', '').strip()

            # Handle avatar upload
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            profile.save()

            messages.success(request, 'Profile updated successfully.')

        elif action == 'password':
            current_pw = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm_pw = request.POST.get('confirm_password', '')

            if not user.check_password(current_pw):
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm_pw:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                user.set_password(new_pw)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')

        return redirect('dashboard:settings')

    context = {
        'page_title': 'Settings',
        'profile': profile,
    }
    return render(request, 'dashboard/settings.html', context)
