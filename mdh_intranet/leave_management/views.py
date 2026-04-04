from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import LeaveRequest, LeaveType
from .forms import LeaveRequestForm, LeaveApprovalForm

@login_required
def leave_list(request):
    """List of leave requests - User's own or staff overview."""
    if request.user.is_staff:
        # Staff sees all, with pending items first
        pending_leaves = LeaveRequest.objects.filter(status='PENDING').order_by('-created_at')
        other_leaves = LeaveRequest.objects.exclude(status='PENDING').order_by('-created_at')
        my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-created_at')
    else:
        pending_leaves = None
        other_leaves = None
        my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'my_leaves': my_leaves,
        'pending_leaves': pending_leaves,
        'other_leaves': other_leaves,
        'leave_types': LeaveType.objects.filter(is_active=True),
    }
    return render(request, 'leave_management/leave_list.html', context)

@login_required
def leave_create(request):
    """Submit a new leave request."""
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            
            # Notify Admins/Staff
            from mdh_intranet.core.services import notify_admins
            notify_admins(
                title="New Leave Request Submitted",
                notification_type="leave",
                message=f"{request.user.username} has requested {leave.leave_type.name} from {leave.start_date} to {leave.end_date}.",
                link=f"/leave/{leave.pk}/",
                priority="high",
            )
            
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_management:leave_list')
    else:
        form = LeaveRequestForm()
    
    return render(request, 'leave_management/leave_form.html', {'form': form, 'title': 'Apply for Leave'})

@login_required
def leave_detail(request, pk):
    """View details of a leave request."""
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    # Permission check
    if not (request.user.is_staff or request.user == leave.user):
        messages.error(request, 'Access denied.')
        return redirect('leave_management:leave_list')
    
    context = {
        'leave': leave,
        'approval_form': LeaveApprovalForm(instance=leave) if request.user.is_staff and leave.status == 'PENDING' else None
    }
    return render(request, 'leave_management/leave_detail.html', context)

@login_required
def leave_approve(request, pk):
    """Handle leave approval/rejection (Staff only)."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('leave_management:leave_list')
    
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        form = LeaveApprovalForm(request.POST, instance=leave)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            
            from mdh_intranet.core.services import notify
            is_approved = approval.status == 'APPROVED'
            notify(
                recipient=leave.user,
                title=f"Leave Request {approval.get_status_display()}",
                notification_type='approved' if is_approved else 'rejected',
                message=f"Your {leave.leave_type.name} request for {leave.start_date} has been {approval.get_status_display().lower()}.",
                link=f"/leave/{leave.pk}/",
                priority='high' if not is_approved else 'normal',
                send_email=True
            )
            
            messages.success(request, f'Leave request for {leave.user.username} has been {leave.get_status_display().lower()}.')
            return redirect('leave_management:leave_detail', pk=pk)
    
    return redirect('leave_management:leave_detail', pk=pk)
