from django.http import JsonResponse
from django.db.models import Q
from .models import ICDCode

def search_icd_codes(request):
    """
    Search endpoint for ICD-11 codes.
    Returns: JSON {results: [{id: code, text: description, chapter: ...}]}
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    # Search in both code and description
    codes = ICDCode.objects.filter(
        Q(code__icontains=query) | Q(description__icontains=query)
    ).only('code', 'description', 'chapter')[:25] # Limit results for performance

    results = [
        {
            'id': c.code,
            'text': f"{c.code} - {c.description}",
            'code': c.code,
            'description': c.description,
            'chapter': c.chapter
        } for c in codes
    ]

    return JsonResponse({'results': results})
