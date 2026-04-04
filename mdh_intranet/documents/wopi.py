import json
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import Document

WOPI_PROOF = "dummy-token"  # replace with real auth later

@csrf_exempt
def check_file_info(request, file_id):
    try:
        doc = Document.objects.get(id=file_id)
    except Document.DoesNotExist:
        print(f"Document {file_id} not found")
        return HttpResponse(status=404)
    
    try:
        # Get file basename
        filename = doc.file.name.split("/")[-1]
        
        # Get file size
        file_size = doc.file.size if hasattr(doc.file, 'size') else 0
        
        # Get timestamp - use updated_at if available, otherwise created_at or current time
        if hasattr(doc, 'updated_at') and doc.updated_at:
            version = str(doc.updated_at.timestamp())
        elif hasattr(doc, 'uploaded_at') and doc.uploaded_at:
            version = str(doc.uploaded_at.timestamp())
        else:
            from django.utils import timezone
            version = str(timezone.now().timestamp())
        
        info = {
            "BaseFileName": filename,
            "Size": file_size,
            "UserId": str(request.user.id if request.user.is_authenticated else "guest"),
            "UserFriendlyName": request.user.username if request.user.is_authenticated else "Guest",
            "Version": version,
            "SupportsUpdate": True,
            "SupportsLocks": False,
            "UserCanWrite": True,
        }
        
        print(f"WOPI CheckFileInfo for file {file_id}: {info}")
        return JsonResponse(info)
        
    except Exception as e:
        print(f"Error in check_file_info: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(status=500)


@csrf_exempt
def get_file(request, file_id):
    try:
        doc = Document.objects.get(id=file_id)
    except Document.DoesNotExist:
        return HttpResponse(status=404)

    with open(doc.file.path, "rb") as f:
        return HttpResponse(f.read(), content_type="application/octet-stream")


@csrf_exempt
def put_file(request, file_id):
    if request.method != "POST":
        return HttpResponseForbidden()

    try:
        doc = Document.objects.get(id=file_id)
    except Document.DoesNotExist:
        return HttpResponse(status=404)

    # Save updated file
    with open(doc.file.path, "wb") as f:
        f.write(request.body)

    return HttpResponse(status=200)


@csrf_exempt
def file_contents(request, file_id):
    """Dispatcher for WOPI GetFile (GET) and PutFile (POST)"""
    if request.method == "POST":
        return put_file(request, file_id)
    else:
        return get_file(request, file_id)

