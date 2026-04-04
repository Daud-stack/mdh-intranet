from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import AuditTemplate, AuditQuestion, AuditSubmission, AuditAnswer
from .forms import AuditSubmissionForm

@login_required
def dashboard(request):
    templates = AuditTemplate.objects.filter(is_active=True).order_by('-created_at')
    recent_audits = AuditSubmission.objects.all().order_by('-conducted_at')[:10]
    
    # Simple analytics
    total_audits = AuditSubmission.objects.count()
    overall_score = 0
    if total_audits > 0:
        total_score = sum([a.score for a in AuditSubmission.objects.all()])
        total_possible = sum([a.template.questions.count() for a in AuditSubmission.objects.all()])
        if total_possible > 0:
            overall_score = int((total_score / total_possible) * 100)
            
    context = {
        'templates': templates,
        'recent_audits': recent_audits,
        'overall_score': overall_score,
        'total_audits': total_audits,
    }
    return render(request, 'quality_audit/dashboard.html', context)

@login_required
def perform_audit(request, template_id):
    template = get_object_or_404(AuditTemplate, id=template_id, is_active=True)
    questions = template.questions.all()
    
    if not questions.exists():
        messages.error(request, "This audit template has no questions configured.")
        return redirect('quality_audit:dashboard')

    if request.method == 'POST':
        form = AuditSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.template = template
            submission.auditor = request.user
            submission.save()
            
            score = 0
            for q in questions:
                passed = request.POST.get(f'q_{q.id}') == 'yes'
                comments = request.POST.get(f'notes_{q.id}', '')
                AuditAnswer.objects.create(
                    submission=submission,
                    question=q,
                    passed=passed,
                    comments=comments
                )
                if passed:
                    score += 1
                    
            submission.score = score
            submission.save()
            
            messages.success(request, f"Audit submitted successfully! Score: {score}/{questions.count()}")
            return redirect('quality_audit:audit_detail', submission_id=submission.id)
    else:
        form = AuditSubmissionForm(initial={'department_audited': template.department_target})
        
    return render(request, 'quality_audit/perform_audit.html', {
        'template': template,
        'questions': questions,
        'form': form
    })

@login_required
def audit_detail(request, submission_id):
    submission = get_object_or_404(AuditSubmission, id=submission_id)
    answers = submission.answers.all()
    
    max_score = submission.template.questions.count()
    score_percentage = 0
    if max_score > 0:
        score_percentage = int((submission.score / max_score) * 100)
        
    return render(request, 'quality_audit/audit_detail.html', {
        'submission': submission,
        'answers': answers,
        'max_score': max_score,
        'score_percentage': score_percentage
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def template_create(request):
    """Create a new audit template."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        dept = request.POST.get('department_target')
        
        template = AuditTemplate.objects.create(
            title=title, 
            description=description, 
            department_target=dept
        )
        messages.success(request, f"Template '{title}' created. Now add questions.")
        return redirect('quality_audit:template_questions', template_id=template.id)
    
    return render(request, 'quality_audit/template_form.html')


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def template_questions(request, template_id):
    """Add/Edit questions for an audit template."""
    template = get_object_or_404(AuditTemplate, id=template_id)
    questions = template.questions.all()
    
    if request.method == 'POST':
        if 'add_question' in request.POST:
            text = request.POST.get('text')
            order = request.POST.get('order', 0)
            AuditQuestion.objects.create(template=template, text=text, order=order)
            messages.success(request, "Question added.")
        elif 'delete_question' in request.POST:
            qid = request.POST.get('question_id')
            AuditQuestion.objects.filter(id=qid, template=template).delete()
            messages.success(request, "Question removed.")
            
        return redirect('quality_audit:template_questions', template_id=template.id)
        
    return render(request, 'quality_audit/template_questions.html', {
        'template': template,
        'questions': questions
    })


@login_required
def export_audit_pdf(request, submission_id):
    """Export audit results as a PDF report."""
    from io import BytesIO
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    submission = get_object_or_404(AuditSubmission, id=submission_id)
    answers = submission.answers.all().select_related('question')
    
    max_score = submission.template.questions.count()
    score_percentage = 0
    if max_score > 0:
        score_percentage = int((submission.score / max_score) * 100)
        
    html_content = render_to_string('quality_audit/audit_pdf_report.html', {
        'submission': submission,
        'answers': answers,
        'max_score': max_score,
        'score_percentage': score_percentage,
        'generated_at': timezone.now()
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)
    
    if pisa_status.err:
        messages.error(request, "Failed to generate PDF report.")
        return redirect('quality_audit:audit_detail', submission_id=submission_id)
        
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"Audit_{submission.id}_{submission.department_audited}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
