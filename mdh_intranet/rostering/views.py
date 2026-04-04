from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Roster, Shift, ShiftAssignment, ShiftSwapRequest, ShiftTemplate
from .forms import RosterForm, SwapRequestForm
from django.db.models import Count

@login_required
def dashboard(request):
    """Rostering Manager Dashboard"""
    today = timezone.now().date()
    active_rosters = Roster.objects.filter(start_date__lte=today+timedelta(days=30), end_date__gte=today).order_by('start_date')
    pending_swaps = ShiftSwapRequest.objects.filter(status='PENDING')
    
    # Get shifts for today
    todays_shifts = Shift.objects.filter(date=today).annotate(
        assigned_count=Count('assignments')
    )
    
    context = {
        'active_rosters': active_rosters,
        'pending_swaps': pending_swaps,
        'todays_shifts': todays_shifts,
    }
    return render(request, 'rostering/dashboard.html', context)

@login_required
def roster_setup(request):
    """Create or configure a new roster (Ward Managers)"""
    if request.method == 'POST':
        form = RosterForm(request.POST)
        if form.is_valid():
            roster = form.save(commit=False)
            roster.author = request.user
            roster.save()
            messages.success(request, f"New roster for {roster.department} created. Next, add shifts.")
            return redirect('rostering:dashboard')
    else:
        form = RosterForm(initial={'start_date': timezone.now().date()})
        
    return render(request, 'rostering/roster_setup.html', {'form': form})

@login_required
def my_shifts(request):
    """Employee view of their upcoming shifts"""
    assignments = ShiftAssignment.objects.filter(
        employee=request.user, 
        shift__date__gte=timezone.now().date()
    ).order_by('shift__date', 'shift__template__start_time')
    
    swap_form = SwapRequestForm(requester=request.user)
    
    return render(request, 'rostering/my_shifts.html', {
        'assignments': assignments,
        'swap_form': swap_form
    })

@login_required
def swap_requests(request):
    """View and manage swap requests"""
    if request.method == 'POST':
        # Handle swap request action (approve/reject)
        action = request.POST.get('action')
        req_id = request.POST.get('request_id')
        
        if action == 'CREATE':
            form = SwapRequestForm(request.POST, requester=request.user)
            assignment_id = request.POST.get('assignment_id')
            if form.is_valid() and assignment_id:
                swap = form.save(commit=False)
                swap.assignment_id = assignment_id
                swap.requester = request.user
                swap.save()
                messages.success(request, 'Swap request submitted!')
                
                from mdh_intranet.core.services import notify
                notify(
                    recipient=swap.requested_colleague,
                    title="Shift Swap Request",
                    notification_type="alert",
                    message=f"{request.user.username} has asked you to cover a shift on {swap.assignment.shift.date}.",
                    link="/rostering/swap-requests/",
                    priority="high"
                )
            return redirect('rostering:my_shifts')

        if action and req_id:
            swap_req = get_object_or_404(ShiftSwapRequest, id=req_id)
            if action == 'APPROVE':
                swap_req.status = 'APPROVED'
                # Actually perform the swap:
                assignment = swap_req.assignment
                assignment.employee = swap_req.requested_colleague
                assignment.save()
                
                from mdh_intranet.core.services import notify
                notify(
                    recipient=swap_req.requester,
                    title="Shift Swap Approved",
                    notification_type="approved",
                    message=f"{swap_req.requested_colleague.username} has accepted to cover your {assignment.shift.template.name} shift on {assignment.shift.date}.",
                    link="/rostering/my-shifts/",
                    priority="high"
                )
                
                messages.success(request, f"Swap approved! {swap_req.requested_colleague.username} will cover the shift.")
            elif action == 'REJECT':
                swap_req.status = 'REJECTED'
                
                from mdh_intranet.core.services import notify
                notify(
                    recipient=swap_req.requester,
                    title="Shift Swap Rejected",
                    notification_type="rejected",
                    message=f"{swap_req.requested_colleague.username} has declined to cover your shift.",
                    link="/rostering/swap-requests/",
                    priority="normal"
                )
                
                messages.error(request, "Swap request rejected.")
            swap_req.save()
            return redirect('rostering:swap_requests')

    received_requests = ShiftSwapRequest.objects.filter(requested_colleague=request.user, status='PENDING')
    my_requests = ShiftSwapRequest.objects.filter(requester=request.user).order_by('-created_at')
    
    return render(request, 'rostering/swap_requests.html', {
        'received_requests': received_requests,
        'my_requests': my_requests
    })

@login_required
def manage_roster(request, pk):
    """View to manage shifts and staffing for a specific roster"""
    roster = get_object_or_404(Roster, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'publish':
            roster.is_published = True
            roster.save()
            messages.success(request, f"Roster {roster.department} has been published!")
        elif action == 'add_shift':
            template_id = request.POST.get('template_id')
            shift_date = request.POST.get('shift_date')
            required_staff = int(request.POST.get('required_staff', 1))
            
            if template_id and shift_date:
                template = get_object_or_404(ShiftTemplate, pk=template_id)
                Shift.objects.create(
                    roster=roster,
                    date=shift_date,
                    template=template,
                    required_staff=required_staff
                )
                messages.success(request, f"Added {template.name} on {shift_date}")
        elif action == 'assign_staff':
            shift_id = request.POST.get('shift_id')
            employee_id = request.POST.get('employee_id')
            if shift_id and employee_id:
                from django.contrib.auth.models import User
                from .models import ShiftAssignment
                shift = get_object_or_404(Shift, pk=shift_id)
                employee = get_object_or_404(User, pk=employee_id)
                if not ShiftAssignment.objects.filter(shift=shift, employee=employee).exists():
                    ShiftAssignment.objects.create(shift=shift, employee=employee)
                    messages.success(request, f"Assigned {employee.get_full_name() or employee.username} to shift.")
                else:
                    messages.warning(request, f"{employee.get_full_name() or employee.username} is already assigned to this shift.")
                
        return redirect('rostering:manage_roster', pk=pk)
        
    shifts = roster.shifts.all().prefetch_related('assignments', 'assignments__employee', 'template')
    templates = ShiftTemplate.objects.all()
    from django.contrib.auth.models import User
    employees = User.objects.all().order_by('first_name')
    
    return render(request, 'rostering/manage_roster.html', {
        'roster': roster,
        'shifts': shifts,
        'templates': templates,
        'employees': employees
    })
