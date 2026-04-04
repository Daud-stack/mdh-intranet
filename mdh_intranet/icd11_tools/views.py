from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import ICDCode, RecentlyViewedCode
from mdh_intranet.documents.models import Document

@login_required
def index(request):
    """ICD-11 Tools - Medical coding reference"""
    query = request.GET.get('search', '')
    
    # Get mapped documents
    mapped_docs = Document.objects.filter(category__target_app='icd11').select_related('category')
    
    # Get all chapters (group by chapter)
    # Using a distinct query to get unique chapters
    chapters_list = ICDCode.objects.order_by('chapter').values_list('chapter', flat=True).distinct()
    
    # Simple formatting for the view (Chapter X: Name) if available, 
    # but our model just has 'chapter' string.
    chapters = []
    for ch in chapters_list:
        # Get count and range (approx) for display
        count = ICDCode.objects.filter(chapter=ch).count()
        first = ICDCode.objects.filter(chapter=ch).first()
        last = ICDCode.objects.filter(chapter=ch).last()
        chapters.append({
            'name': ch,
            'count': count,
            'range': f"{first.code}-{last.code}" if first and last else ""
        })

    # Recent codes for this user
    recent_codes = RecentlyViewedCode.objects.filter(user=request.user).select_related('code')[:10]
    
    # Search Results
    results = None
    if query:
        results = ICDCode.objects.filter(
            Q(code__icontains=query) | 
            Q(description__icontains=query)
        )[:50] # Limit results
        
        # If single exact match, log it as viewed (optional, or wait for click)
        # For this implementation, let's just show results. The user 'views' it when they click detail.
        # But wait, we don't have a detail page in the plan explicitly, 
        # but we can add one or track clicks. 
        # For simplicity, if they search and find an EXACT code match, we could log it?
        # Better: Add a detail view to track specific code viewing.

    context = {
        'total_codes': ICDCode.objects.count(),
        'active_chapters': len(chapters),
        'recent_codes': recent_codes,
        'chapters': chapters,
        'search_query': query,
        'results': results,
        'mapped_docs': mapped_docs,
    }
    return render(request, 'icd11_tools/index.html', context)

@login_required
def code_detail(request, pk):
    """View details of a specific code and log it"""
    code = get_object_or_404(ICDCode, pk=pk)
    
    # Log as recently viewed
    # Update existing or create new
    RecentlyViewedCode.objects.update_or_create(
        user=request.user,
        code=code,
        defaults={'viewed_at': timezone.now()}
    )
    
    # Since we don't have a dedicated page, we render the index with this code focused
    # OR we can just return a simple modal snippet? 
    # Let's verify what the users wants. The plan said 'index.html' modification mostly.
    # Let's redirect to index with a 'selected_code' param?
    # Or just render a simple detail template. Let's create a minimal detail template.
    
    context = {'code': code}
    return render(request, 'icd11_tools/detail.html', context)
