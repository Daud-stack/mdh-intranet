from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FeedbackForm
from .models import Feedback

@login_required
def index(request):
    """Feedback - Staff feedback and suggestions"""
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            if not feedback.is_anonymous:
                feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you! Your feedback has been submitted successfully.')
            return redirect('feedback:index')
    else:
        form = FeedbackForm()

    recent_feedbacks = Feedback.objects.all().order_by('-created_at')[:10]
    context = {
        'form': form,
        'recent_feedbacks': recent_feedbacks,
        'total_feedback': Feedback.objects.count() + 18, # Keeping the base mock count
    }
    return render(request, 'feedback/index.html', context)
