from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TrainingCourse, Certification
from .forms import CertificationForm

@login_required
def dashboard(request):
    """Personal compliance dashboard showing all completed/expired courses for the user."""
    certifications = Certification.objects.filter(employee=request.user).order_by('-date_completed')
    
    # Calculate expiring in 30 days or expired
    thirty_days_from_now = timezone.now().date() + timezone.timedelta(days=30)
    
    expired = []
    expiring_soon = []
    valid = []
    
    for cert in certifications:
        if cert.is_expired():
            expired.append(cert)
        elif cert.expiry_date and cert.expiry_date <= thirty_days_from_now:
            expiring_soon.append(cert)
        else:
            valid.append(cert)
            
    # Check mandatory missing courses
    mandatory_courses = TrainingCourse.objects.filter(is_mandatory=True)
    completed_mandatory_ids = [c.course.id for c in valid + expiring_soon]
    missing_mandatory = mandatory_courses.exclude(id__in=completed_mandatory_ids)

    context = {
        'certifications': certifications,
        'expired': expired,
        'expiring_soon': expiring_soon,
        'valid': valid,
        'missing_mandatory': missing_mandatory,
        'compliance_score': 0 if not mandatory_courses.count() else int((len(valid) + len(expiring_soon)) / mandatory_courses.count() * 100),
    }
    return render(request, 'training_compliance/dashboard.html', context)

@login_required
def log_certification(request):
    """Upload a completed certificate."""
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.employee = request.user
            
            # Note: if there's already an existing unexpired certification for this course, we
            # might want to allow this as a "renewal", so we just save it as a new record.
            cert.save()
            messages.success(request, f"Successfully logged completion for {cert.course.title}.")
            return redirect('training_compliance:dashboard')
    else:
        form = CertificationForm()
    return render(request, 'training_compliance/log_certification.html', {'form': form})

@login_required
def course_directory(request):
    """Browse all available and mandatory training courses."""
    courses = TrainingCourse.objects.all().order_by('-is_mandatory', 'title')
    return render(request, 'training_compliance/course_directory.html', {'courses': courses})
