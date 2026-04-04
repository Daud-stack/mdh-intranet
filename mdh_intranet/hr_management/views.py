from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Attendance, PerformanceReview, TrainingRecord, HiringRequest
from .forms import PerformanceReviewForm, TrainingRecordForm, StaffCreationForm, HiringRequestForm
from mdh_intranet.user_management.models import UserProfile
from django.db.models import Count, Avg

@login_required
def hr_dashboard(request):
    """General HR Overview"""
    staff_count = User.objects.count()
    active_attendance = Attendance.objects.filter(date=timezone.now().date()).count()
    recent_reviews = PerformanceReview.objects.order_by('-created_at')[:5]
    hiring_request_count = HiringRequest.objects.filter(status='PENDING').count()
    
    context = {
        'staff_count': staff_count,
        'active_attendance': active_attendance,
        'recent_reviews': recent_reviews,
        'hiring_request_count': hiring_request_count,
    }
    return render(request, 'hr_management/dashboard.html', context)

@login_required
def employee_list(request):
    """Directory of all employees"""
    employees = User.objects.select_related('profile').all().order_by('last_name')
    return render(request, 'hr_management/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    """Detailed profile of one employee"""
    employee = get_object_or_404(User, pk=pk)
    attendance = Attendance.objects.filter(user=employee).order_by('-date')[:30]
    reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')
    training = TrainingRecord.objects.filter(employee=employee).order_by('-completion_date')
    
    context = {
        'employee': employee,
        'attendance': attendance,
        'reviews': reviews,
        'training': training,
        'today': timezone.now().date(),
    }
    return render(request, 'hr_management/employee_detail.html', context)

@login_required
def attendance_list(request):
    """Recent attendance logs"""
    logs = Attendance.objects.all().select_related('user').order_by('-date', '-clock_in')[:100]
    today_log = Attendance.objects.filter(user=request.user, date=timezone.now().date()).first()
    
    return render(request, 'hr_management/attendance_list.html', {
        'logs': logs,
        'today_log': today_log
    })

@login_required
def clock_in(request):
    """Action: Clock in for today"""
    today = timezone.now().date()
    attendance, created = Attendance.objects.get_or_create(user=request.user, date=today)
    
    if not attendance.clock_in:
        attendance.clock_in = timezone.now().time()
        attendance.save()
        messages.success(request, "Successfully clocked in.")
    else:
        messages.warning(request, "You are already clocked in.")
        
    return redirect('hr_management:attendance_list')

@login_required
def clock_out(request):
    """Action: Clock out for today"""
    today = timezone.now().date()
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    if attendance and not attendance.clock_out:
        attendance.clock_out = timezone.now().time()
        attendance.save()
        messages.success(request, "Successfully clocked out.")
    else:
        messages.warning(request, "Cannot clock out. Either not clocked in or already clocked out.")
        
    return redirect('hr_management:attendance_list')

@login_required
def performance_list(request):
    """List of all performance reviews"""
    if request.user.is_staff:
        reviews = PerformanceReview.objects.all().select_related('employee', 'reviewer').order_by('-review_date')
    else:
        reviews = PerformanceReview.objects.filter(employee=request.user).order_by('-review_date')
        
    return render(request, 'hr_management/performance_list.html', {'reviews': reviews})

@user_passes_test(lambda u: u.is_staff)
def performance_create(request, employee_id):
    """Create a new review (Admin Only)"""
    employee = get_object_or_404(User, pk=employee_id)
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.employee = employee
            review.reviewer = request.user
            review.save()
            messages.success(request, f"Review created for {employee.get_full_name() or employee.username}")
            return redirect('hr_management:employee_detail', pk=employee.pk)
    else:
        form = PerformanceReviewForm(initial={'review_date': timezone.now().date()})
        
    return render(request, 'hr_management/performance_form.html', {'employee': employee, 'form': form})

@login_required
def training_list(request):
    """List of all training records"""
    if request.user.is_staff:
        records = TrainingRecord.objects.all().select_related('employee').order_by('-completion_date')
    else:
        records = TrainingRecord.objects.filter(employee=request.user).order_by('-completion_date')
        
    return render(request, 'hr_management/training_list.html', {
        'records': records,
        'today': timezone.now().date(),
    })

@user_passes_test(lambda u: u.is_staff)
def training_create(request, employee_id):
    """Record a completed training (Admin Only)"""
    employee = get_object_or_404(User, pk=employee_id)
    if request.method == 'POST':
        form = TrainingRecordForm(request.POST, request.FILES)
        if form.is_valid():
            training = form.save(commit=False)
            training.employee = employee
            training.save()
            messages.success(request, f"Training recorded for {employee.get_full_name() or employee.username}")
            return redirect('hr_management:employee_detail', pk=employee.pk)
    else:
        form = TrainingRecordForm(initial={'completion_date': timezone.now().date()})
        
    return render(request, 'hr_management/training_form.html', {'employee': employee, 'form': form})



@user_passes_test(lambda u: u.is_staff)
def employee_create(request):
    """Create a new employee (Admin Only)"""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Employee {user.get_full_name() or user.username} created successfully.")
            return redirect('hr_management:employee_list')
    else:
        form = StaffCreationForm()
        
    return render(request, 'hr_management/employee_form.html', {'form': form})

@login_required
def hiring_request_list(request):
    """List of hiring requests"""
    if request.user.is_staff:
        requests = HiringRequest.objects.all().order_by('-created_at')
    else:
        requests = HiringRequest.objects.filter(requester=request.user).order_by('-created_at')
    return render(request, 'hr_management/hiring_request_list.html', {'requests': requests})

@login_required
def hiring_request_create(request):
    """Submit a new request to employ"""
    if request.method == 'POST':
        form = HiringRequestForm(request.POST)
        if form.is_valid():
            hiring_req = form.save(commit=False)
            hiring_req.requester = request.user
            hiring_req.save()
            
            from mdh_intranet.core.services import notify_admins
            notify_admins(
                title="New Hiring Request",
                notification_type="approval",
                message=f"{request.user.username} requested to hire a {hiring_req.position_title} for {hiring_req.department}.",
                link=f"/hr/hiring/",
                priority="high"
            )
            
            messages.success(request, "Hiring request submitted successfully.")
            return redirect('hr_management:hiring_request_list')
    else:
        initial_data = {}
        if hasattr(request.user, 'profile'):
            initial_data['department'] = request.user.profile.department
        form = HiringRequestForm(initial=initial_data)
    
    return render(request, 'hr_management/hiring_request_form.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def hiring_request_status_update(request, pk, status):
    """Approve or Reject a hiring request (Admin Only)"""
    hiring_req = get_object_or_404(HiringRequest, pk=pk)
    if status in ['APPROVED', 'REJECTED', 'COMPLETED']:
        hiring_req.status = status
        hiring_req.save()
        
        from mdh_intranet.core.services import notify
        notify(
            recipient=hiring_req.requester,
            title=f"Hiring Request {status.title()}",
            notification_type="approved" if status == "APPROVED" else "rejected",
            message=f"Your request to hire a {hiring_req.position_title} has been marked as {status}.",
            link=f"/hr/hiring/",
            priority="normal"
        )
        
        messages.success(request, f"Hiring request marked as {status}.")
    return redirect('hr_management:hiring_request_list')
