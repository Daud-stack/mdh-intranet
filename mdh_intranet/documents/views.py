from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Document, DocumentCategory
from .forms import DocumentUploadForm, SOPGeneratorForm
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone
from urllib.parse import quote_plus
import mammoth
import os
import io


@login_required
def index(request):
    """Document management dashboard"""
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    # Base queryset - filter by access
    if request.user.is_staff:
        documents = Document.objects.all()
    else:
        documents = Document.objects.filter(is_public=True)
    
    # Apply filters
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    if category_id:
        if str(category_id).isdigit():
            documents = documents.filter(category_id=category_id)
        else:
            # Handle category name strings (e.g. from dashboard links)
            documents = documents.filter(category__name__icontains=category_id)
    
    # Get categories with counts
    categories = DocumentCategory.objects.all()
    
    context = {
        'documents': documents[:20],  # Latest 20
        'categories': categories,
        'total_documents': Document.objects.count(),
        'search_query': search,
        'selected_category': category_id,
    }
    return render(request, 'documents/index.html', context)


@login_required
def upload_document(request):
    """Upload a new document - staff only"""
    if not request.user.is_staff:
        messages.error(request, 'Only staff members can upload documents.')
        return redirect('documents:index')
    
    if request.method == 'POST':
        print(f"DEBUG: POST data: {request.POST}")
        print(f"DEBUG: FILES data: {request.FILES}")
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'Document "{document.title}" uploaded successfully!')
            return redirect('documents:index')
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            messages.error(request, f"Upload failed: {form.errors.as_text()}")
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
    }
    return render(request, 'documents/upload.html', context)


@login_required
def download_document(request, pk):
    """Download a document and increment counter"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check access rights
    if not document.is_public and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('documents:index')
    
    # Increment download counter
    document.downloads += 1
    document.save(update_fields=['downloads'])
    
    # Serve file
    try:
        response = FileResponse(document.file.open('rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
        return response
    except Exception as e:
        messages.error(request, 'Error downloading file.')
        return redirect('documents:index')


@login_required
def delete_document(request, pk):
    """Delete a document - staff only or owner"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or document.uploaded_by == request.user):
        messages.error(request, 'You do not have permission to delete this document.')
        return redirect('documents:index')
    
    if request.method == 'POST':
        title = document.title
        # Delete file from filesystem
        document.file.delete()
        # Delete database record
        document.delete()
        messages.success(request, f'Document "{title}" deleted successfully.')
        return redirect('documents:index')
    
    context = {
        'document': document,
    }
    return render(request, 'documents/delete_confirm.html', context)


@login_required
def document_detail(request, pk):
    """View document details"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check access rights
    if not document.is_public and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('documents:index')
    
    context = {
        'document': document,
        'can_delete': request.user.is_staff or document.uploaded_by == request.user,
    }
    return render(request, 'documents/detail.html', context)


@login_required
def view_word_document(request, pk):
    """View Word document in browser with HTML conversion - preserving original format"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check access rights
    if not document.is_public and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('documents:index')
    
    # Check if it's a Word document
    file_ext = os.path.splitext(document.file.name)[1].lower()
    is_word = file_ext in ['.docx', '.doc']
    
    html_content = None
    error_message = None
    is_large_document = False
    initial_content = None
    
    # Check file size - if > 500KB, use lazy loading
    file_size_kb = document.file.size / 1024 if document.file else 0
    is_large_document = file_size_kb > 500  # 500KB threshold
    
    if is_word and file_ext == '.docx':
        if is_large_document:
            # For large documents, only load first page initially
            initial_content = "<p class='text-muted'><i class='fas fa-spinner fa-spin me-2'></i>Loading document...</p>"
        else:
            try:
                with document.file.open('rb') as docx_file:
                    # Enhanced style mapping to preserve Word formatting
                    style_map = """
                        p[style-name='Heading 1'] => h1:fresh
                        p[style-name='Heading 2'] => h2:fresh
                        p[style-name='Heading 3'] => h3:fresh
                        p[style-name='Heading 4'] => h4:fresh
                        p[style-name='Title'] => h1.document-title:fresh
                        p[style-name='Subtitle'] => h2.document-subtitle:fresh
                        p[style-name='Quote'] => blockquote:fresh
                        p[style-name='List Paragraph'] => li:fresh
                        r[style-name='Strong'] => strong
                        r[style-name='Emphasis'] => em
                        r[style-name='Hyperlink'] => a
                        table => table.word-table
                        b => strong
                        i => em
                        u => u
                    """
                    
                    # Image converter function
                    def convert_image(image):
                        import base64
                        with image.open() as image_bytes:
                            encoded = base64.b64encode(image_bytes.read()).decode('ascii')
                        return {"src": f"data:{image.content_type};base64,{encoded}"}
                    
                    # Convert with style preservation and image embedding
                    result = mammoth.convert_to_html(
                        docx_file,
                        style_map=style_map,
                        convert_image=mammoth.images.img_element(convert_image)
                    )
                    html_content = result.value
                    
                    # Post-process to add inline styles for better formatting
                    html_content = post_process_word_html(html_content)
                    
                    if result.messages:
                        for msg in result.messages:
                            print(f"Mammoth: {msg.message}")
                            
            except Exception as e:
                error_message = f"Error converting document: {str(e)}"
                import traceback
                traceback.print_exc()
    elif file_ext == '.doc':
        error_message = "Legacy .doc format is not supported. Please upload a .docx file."
    else:
        error_message = "This viewer only supports Word documents (.docx)"
    
    context = {
        'document': document,
        'html_content': html_content if not is_large_document else initial_content,
        'error_message': error_message,
        'is_word': is_word,
        'can_edit': request.user.is_staff,
        'is_large_document': is_large_document,
        'is_large_document_js': 'true' if is_large_document else 'false',
        'file_size_kb': round(file_size_kb, 1),
    }
    return render(request, 'documents/word_viewer.html', context)



def post_process_word_html(html):
    """Post-process HTML to enhance Word formatting preservation"""
    import re
    
    if not html:
        return html
    
    # Ensure tables have proper styling (only if not already styled)
    if '<table>' in html:
        html = html.replace('<table>', '<table class="word-table" style="width:100%; border-collapse:collapse; margin:12pt 0; border:1px solid #000;">')
    if '<th>' in html:
        html = html.replace('<th>', '<th style="border:1px solid #000; padding:8pt 10pt; background:#d9e2f3; font-weight:bold; text-align:left;">')
    if '<td>' in html:
        html = html.replace('<td>', '<td style="border:1px solid #000; padding:8pt 10pt; vertical-align:top;">')
    
    # Make links clickable and styled with Word's default blue
    html = re.sub(
        r'<a href="([^"]+)"(?![^>]*style)',
        r'<a href="\1" target="_blank" rel="noopener" style="color:#0563C1; text-decoration:underline;"',
        html
    )
    
    # Style headings (only if not already styled)
    if '<h1>' in html:
        html = html.replace('<h1>', '<h1 style="font-size:22pt; font-weight:bold; margin:24pt 0 12pt; color:#2F5496; font-family:Calibri Light, sans-serif;">')
    if '<h2>' in html:
        html = html.replace('<h2>', '<h2 style="font-size:16pt; font-weight:bold; margin:18pt 0 9pt; color:#2F5496; font-family:Calibri Light, sans-serif;">')
    if '<h3>' in html:
        html = html.replace('<h3>', '<h3 style="font-size:14pt; font-weight:bold; margin:14pt 0 7pt; color:#1F3864; font-family:Calibri Light, sans-serif;">')
    if '<h4>' in html:
        html = html.replace('<h4>', '<h4 style="font-size:12pt; font-weight:bold; font-style:italic; margin:12pt 0 6pt; color:#2F5496;">')
    
    # Style paragraphs (preserve any existing inline styles)
    if '<p>' in html:
        html = html.replace('<p>', '<p style="margin:0 0 10pt 0; line-height:1.5; font-family:Calibri, sans-serif; font-size:11pt;">')
    
    # Style lists
    if '<ul>' in html:
        html = html.replace('<ul>', '<ul style="margin:0 0 12pt 0; padding-left:36pt; font-family:Calibri, sans-serif;">')
    if '<ol>' in html:
        html = html.replace('<ol>', '<ol style="margin:0 0 12pt 0; padding-left:36pt; font-family:Calibri, sans-serif;">')
    if '<li>' in html:
        html = html.replace('<li>', '<li style="margin-bottom:6pt;">')
    
    # Style blockquotes (Word "Quote" style)
    if '<blockquote>' in html:
        html = html.replace('<blockquote>', '<blockquote style="border-left:4px solid #5B9BD5; padding:10pt 16pt; margin:12pt 0 12pt 24pt; color:#404040; font-style:italic; background:#f8f9fa;">')
    
    # Preserve bold and italic
    if '<strong>' in html:
        html = html.replace('<strong>', '<strong style="font-weight:bold;">')
    if '<em>' in html:
        html = html.replace('<em>', '<em style="font-style:italic;">')
    
    # Handle underline
    if '<u>' in html:
        html = html.replace('<u>', '<u style="text-decoration:underline;">')
    
    # Handle strikethrough
    if '<s>' in html:
        html = html.replace('<s>', '<s style="text-decoration:line-through;">')
    
    # Style images
    html = re.sub(
        r'<img([^>]*)>',
        r'<img\1 style="max-width:100%; height:auto; display:block; margin:12pt auto;">',
        html
    )
    
    # Clean up empty paragraphs but keep line breaks
    html = re.sub(r'<p[^>]*>\s*</p>', '<p style="margin:0; line-height:1.5;">&nbsp;</p>', html)
    
    return html


@login_required
def edit_word_document(request, pk):
    """Edit Word document with rich text editor - preserving format"""
    document = get_object_or_404(Document, pk=pk)
    
    # Staff only
    if not request.user.is_staff:
        messages.error(request, 'Only staff members can edit documents.')
        return redirect('documents:index')
    
    file_ext = os.path.splitext(document.file.name)[1].lower()
    
    if file_ext != '.docx':
        messages.error(request, 'Only .docx files can be edited.')
        return redirect('documents:view_word', pk=pk)
    
    # Check file size
    file_size_kb = document.file.size / 1024 if document.file else 0
    is_large_document = file_size_kb > 500  # 500KB threshold
    
    html_content = None
    try:
        with document.file.open('rb') as docx_file:
            # Enhanced conversion with style preservation
            style_map = """
                p[style-name='Heading 1'] => h1:fresh
                p[style-name='Heading 2'] => h2:fresh
                p[style-name='Heading 3'] => h3:fresh
                p[style-name='Heading 4'] => h4:fresh
                p[style-name='Title'] => h1.document-title:fresh
                p[style-name='Quote'] => blockquote:fresh
                table => table.word-table
                b => strong
                i => em
                u => u
            """
            
            # Image converter function - skip for large docs
            if is_large_document:
                def convert_image(image):
                    return {"src": "#", "alt": "[Image - download original to view]"}
            else:
                def convert_image(image):
                    import base64
                    with image.open() as image_bytes:
                        encoded = base64.b64encode(image_bytes.read()).decode('ascii')
                    return {"src": f"data:{image.content_type};base64,{encoded}"}
            
            result = mammoth.convert_to_html(
                docx_file,
                style_map=style_map,
                convert_image=mammoth.images.img_element(convert_image)
            )
            html_content = result.value
            
            # Apply inline styles for editing
            html_content = post_process_word_html(html_content)
            
    except Exception as e:
        messages.error(request, f'Error loading document: {str(e)}')
        return redirect('documents:detail', pk=pk)
    
    context = {
        'document': document,
        'html_content': html_content,
        'is_large_document': is_large_document,
        'file_size_kb': round(file_size_kb, 1),
    }
    return render(request, 'documents/word_editor.html', context)


@login_required
@require_POST
def save_word_document(request, pk):
    """Save edited Word document content - supports both DOCX blob and HTML content"""
    document = get_object_or_404(Document, pk=pk)
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        import io
        
        # Check if a DOCX file was uploaded (from Syncfusion)
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            
            # Read the uploaded DOCX file
            file_content = uploaded_file.read()
            buffer = io.BytesIO(file_content)
            
            # Save to the document's file field
            document.file.save(document.file.name, buffer, save=True)
            
            # Clear cache
            cache.delete(f'doc_content_{document.pk}')
            
            return JsonResponse({'success': True, 'message': 'Document saved successfully!'})
        
        # Fallback: Handle HTML content (from fallback editor)
        html_content = request.POST.get('content', '')
        
        if not html_content:
            return JsonResponse({'success': False, 'error': 'No content provided'})
        
        # Convert HTML back to DOCX
        try:
            from htmldocx import HtmlToDocx
            from mdh_intranet.sop_manual.export_utils import preprocess_html_for_docx
            
            html_content = preprocess_html_for_docx(html_content)
            
            new_parser = HtmlToDocx()
            docx = new_parser.parse_html_string(html_content)
            
            # Save to buffer
            buffer = io.BytesIO()
            docx.save(buffer)
            buffer.seek(0)
            
            # Save to file
            document.file.save(document.file.name, buffer, save=True)
            
            # Clear cache
            cache.delete(f'doc_content_{document.pk}')
            
            return JsonResponse({'success': True, 'message': 'Document saved successfully!'})
        
        except ImportError:
            return JsonResponse({'success': False, 'error': 'htmldocx library not installed. Please install with: pip install htmldocx'})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_document_content(request, pk):
    """Get paginated document content for lazy loading large documents"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check access
    if not document.is_public and not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        page = int(request.GET.get('page', 1))
        # Default 50 blocks per page for granular loading
        per_page = int(request.GET.get('per_page', 50))
    except (ValueError, TypeError):
        page = 1
        per_page = 50
    
    file_ext = os.path.splitext(document.file.name)[1].lower()
    
    if file_ext != '.docx':
        return JsonResponse({'error': 'Only .docx files supported'}, status=400)
    
    try:
        # Check cache first
        cache_key = f'doc_content_{document.pk}'
        html_content = cache.get(cache_key)
        
        if not html_content:
            with document.file.open('rb') as docx_file:
                style_map = """
                    p[style-name='Heading 1'] => h1:fresh
                    p[style-name='Heading 2'] => h2:fresh
                    p[style-name='Heading 3'] => h3:fresh
                    p[style-name='Heading 4'] => h4:fresh
                    p[style-name='Title'] => h1.document-title:fresh
                    p[style-name='Quote'] => blockquote:fresh
                    table => table.word-table
                    b => strong
                    i => em
                    u => u
                """
                
                # For large documents lazy loading, skip image embedding to improve performance
                result = mammoth.convert_to_html(
                    docx_file,
                    style_map=style_map,
                    convert_image=mammoth.images.img_element(
                        lambda image: {"src": "#", "alt": ""}
                    )
                )
                html_content = result.value
                html_content = post_process_word_html(html_content)
                
                # Cache the converted content (forever until updated)
                cache.set(cache_key, html_content, None)
            
        # Split into sections by block elements
        import re
        sections = re.split(r'(?=<h[1-6][^>]*>|<p[^>]*>|<div[^>]*>|<table[^>]*>|<ul[^>]*>|<ol[^>]*>|<blockquote[^>]*>)', html_content, flags=re.IGNORECASE)
        sections = [s.strip() for s in sections if s.strip()]
        
        total_sections = len(sections)
        total_pages = (total_sections + per_page - 1) // per_page
        
        # Ensure page is valid
        if page < 1: page = 1
        if page > total_pages and total_pages > 0: page = total_pages
        
        # Get the requested page of sections
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_sections = sections[start_idx:end_idx]
        
        # Get table of contents (headings) with page mapping
        toc = []
        if page == 1:
            heading_pattern = re.compile(r'<(h[123])[^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
            for i, section in enumerate(sections):
                match = heading_pattern.search(section)
                if match:
                    tag = match.group(1).lower()
                    text = re.sub(r'<[^>]+>', '', match.group(2)).strip()[:60]
                    if text:
                        # Calculate which page this section belongs to
                        pg = (i // per_page) + 1
                        toc.append({'level': tag, 'text': text, 'page': pg})
        
        return JsonResponse({
            'success': True,
            'html': ''.join(page_sections),
            'page': page,
            'total_pages': total_pages,
            'total_sections': total_sections,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'toc': toc if page == 1 else None,
        })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def create_sop(request):
    """Generate a new SOP document from template"""
    if not request.user.is_staff:
        messages.error(request, "Only staff can generate SOPs.")
        return redirect('documents:index')

    if request.method == 'POST':
        form = SOPGeneratorForm(request.POST)
        if form.is_valid():
            # Prepare context
            context = form.cleaned_data
            context['version_date'] = timezone.now().date()
            
            # Render HTML
            # Render HTML
            try:
                html_content = render_to_string('documents/sop_template.html', context)
                
                # Extract body content for htmldocx (strips html/head/style tags which might appear as text)
                import re
                match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    html_content = match.group(1)
                    
            except Exception as e:
                messages.error(request, f"Error generating template: {e}")
                return render(request, 'documents/sop_create.html', {'form': form})
            
            # Convert to DOCX
            try:
                from htmldocx import HtmlToDocx
                from mdh_intranet.sop_manual.export_utils import preprocess_html_for_docx
                
                html_content = preprocess_html_for_docx(html_content)
                
                new_parser = HtmlToDocx()
                docx = new_parser.parse_html_string(html_content)
                
                buffer = io.BytesIO()
                docx.save(buffer)
                buffer.seek(0)
                
                # Create Document record
                doc = Document(
                    title=form.cleaned_data['sop_title'],
                    category=form.cleaned_data['category'],
                    uploaded_by=request.user,
                    description=f"SOP: {form.cleaned_data['sop_title']} (v{form.cleaned_data['version']})",
                    is_public=False  # SOPs private by default until released
                )
                
                # Generate safe filename
                filename = f"{form.cleaned_data['sop_code']}_v{form.cleaned_data['version']}.docx".replace(" ", "_").replace("/", "-")
                
                doc.file.save(filename, buffer, save=True)
                
                messages.success(request, 'SOP generated successfully! You can now refine tables and formatting in the editor.')
                return redirect('documents:edit_word', pk=doc.pk)
                
            except ImportError:
                 messages.error(request, 'htmldocx library missing. Please install it.')
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error converting to DOCX: {e}")
    else:
        form = SOPGeneratorForm(initial={
            'created_by': request.user.get_full_name() or request.user.username,
            'department': 'Operations',
            'effective_date': timezone.now().date()
        })
    
    return render(request, 'documents/sop_create.html', {'form': form})

@login_required
def collabora_editor(request, doc_id):
    """Launch Collabora Online editor - WOPI enabled"""
    document = get_object_or_404(Document, pk=doc_id)
    
    # Collabora URL (Client)
    # Using 127.0.0.1 for browser access
    collabora_url = "http://127.0.0.1:9980/browser/dist/cool.html"
    
    # WOPISrc - Must be reachable by Collabora container
    # Using host.docker.internal to talk back to Django
    wopi_src = f"http://host.docker.internal:8000/documents/wopi/files/{document.pk}"
    
    # Construct Client URL (no access_token needed with session auth)
    src = f"{collabora_url}?WOPISrc={quote_plus(wopi_src)}"
    print(f"Collabora Launch: {src}")
    
    context = {
        'document': document,
        'collabora_src': src,
        'document_url': request.build_absolute_uri(document.file.url),
    }
    return render(request, 'documents/collabora_view.html', context)


@login_required
def office_web_viewer(request, doc_id):
    """View Office documents using Microsoft Office Web Viewer (Read-Only)"""
    document = get_object_or_404(Document, pk=doc_id)
    
    # Check access rights
    if not document.is_public and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('documents:index')
    
    # Check if file type is supported by Office Web Viewer
    supported_extensions = ['docx', 'xlsx', 'pptx', 'doc', 'xls', 'ppt']
    file_ext = document.file_type.lower()
    
    error = None
    viewer_url = None
    
    if file_ext not in supported_extensions:
        error = f"Microsoft Office Web Viewer does not support .{file_ext} files. Supported formats: Word (.docx), Excel (.xlsx), PowerPoint (.pptx)"
    else:
        # Build the absolute URL to the document
        # Microsoft Office Web Viewer requires a publicly accessible URL
        document_url = request.build_absolute_uri(document.file.url)
        
        # Encode the URL
        from urllib.parse import quote
        encoded_url = quote(document_url, safe='')
        
        # Microsoft Office Web Viewer endpoint
        # Format: https://view.officeapps.live.com/op/embed.aspx?src=<encoded_url>
        viewer_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
        
        print(f"Office Web Viewer URL: {viewer_url}")
        print(f"Document URL: {document_url}")
        
        # Note: For this to work, the document URL must be publicly accessible
        # In development, you might need to use a tunneling service like ngrok
        # or ensure your Django server is accessible from the internet
    
    context = {
        'document': document,
        'viewer_url': viewer_url,
        'error': error,
        'can_edit': request.user.is_staff,
    }
    return render(request, 'documents/office_web_viewer.html', context)
