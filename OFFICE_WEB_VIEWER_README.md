# Microsoft Office Web Viewer Integration

## Overview
The MDH Intranet now supports **Microsoft Office Web Viewer** for viewing Office documents directly in the browser without requiring Microsoft Office installation. This is a free, read-only viewer service provided by Microsoft.

## Features

### ✅ Supported File Types
- **Word Documents**: `.docx`, `.doc`
- **Excel Spreadsheets**: `.xlsx`, `.xls`
- **PowerPoint Presentations**: `.pptx`, `.ppt`

### 🚀 Key Benefits
1. **Free** - No licensing or server setup required
2. **Read-Only** - Perfect for viewing documents without editing
3. **Fast** - Leverages Microsoft's cloud infrastructure
4. **No Installation** - Works directly in the browser
5. **Cross-Platform** - Works on any device with a modern browser

## How It Works

The Microsoft Office Web Viewer uses this URL pattern:
```
https://view.officeapps.live.com/op/embed.aspx?src=<DOCUMENT_URL>
```

Where `<DOCUMENT_URL>` is the publicly accessible URL to your document.

## Usage

### From Document List
1. Navigate to `/documents/`
2. Find an Office document (Word, Excel, or PowerPoint)
3. Click the **👁 View Online** button (gray button)
4. The document will open in the Office Web Viewer

### From Document Detail Page
1. Navigate to any Office document's detail page
2. Click the **👁 View Online** button
3. The document opens in read-only mode

### Quick Access Buttons
- **View Online** (Office Web Viewer) - Read-only viewing
- **Edit in Browser** (Collabora) - Full editing capabilities
- **Download** - Download the file locally

## Important Requirements

### 🌐 Public Accessibility
**CRITICAL**: For Microsoft Office Web Viewer to work, your document URLs must be publicly accessible from the internet. 

#### For Development/Testing:
If you're testing locally (localhost:8000), Microsoft's servers **cannot** access your documents. You have two options:

1. **Use ngrok (Recommended for Testing)**
   ```bash
   # Install ngrok from https://ngrok.com/
   ngrok http 8000
   ```
   Then update your Django `ALLOWED_HOSTS` and use the ngrok URL.

2. **Deploy to a Public Server**
   - Deploy your Django app to a server with a public IP or domain
   - Ensure the `/media/` directory is publicly accessible

#### For Production:
- Ensure your server is accessible from the internet
- Configure proper CORS and security headers
- Make sure `/media/documents/` is publicly accessible

## URL Routes

The following routes have been added:

```python
# View document in Office Web Viewer
/documents/office-viewer/<doc_id>/
```

## Template Integration

### In `detail.html`:
```html
{% if document.file_type in 'docx,xlsx,pptx,doc,xls,ppt' %}
<a href="{% url 'documents:office_web_viewer' document.id %}" class="btn btn-outline-primary">
    <i class="fas fa-eye"></i> View Online
</a>
{% endif %}
```

### In `index.html`:
```html
{% if doc.file_type in 'docx,xlsx,pptx,doc,xls,ppt' %}
<a href="{% url 'documents:office_web_viewer' doc.pk %}" 
   class="btn btn-sm btn-outline-secondary me-1" 
   title="View Online (Office Viewer)">
    <i class="fas fa-eye"></i>
</a>
{% endif %}
```

## Comparison: Office Web Viewer vs Collabora Online

| Feature | Office Web Viewer | Collabora Online |
|---------|------------------|------------------|
| **Cost** | Free | Free (CODE edition) |
| **Setup** | None | Docker required |
| **Editing** | ❌ Read-only | ✅ Full editing |
| **File Support** | Office files only | Office + ODF files |
| **Internet Required** | ✅ Yes | ❌ No (self-hosted) |
| **Performance** | Fast (Microsoft CDN) | Depends on server |
| **Privacy** | Document sent to Microsoft | Fully private |
| **Authentication** | Public URLs only | WOPI protocol |

## When to Use Which?

### Use Office Web Viewer When:
- You need **quick, read-only access**
- You want **zero setup overhead**
- Your documents are **already public** or can be made public
- You're okay with Microsoft processing the document

### Use Collabora Online When:
- You need **editing capabilities**
- You require **complete privacy** (confidential documents)
- You have **sensitive data** that shouldn't leave your server
- You need **offline functionality**

## Troubleshooting

### "Document cannot be loaded" Error
**Cause**: The document URL is not publicly accessible.

**Solutions**:
1. Verify your Django server is accessible from the internet
2. Check that `/media/` files are served correctly
3. For development, use ngrok or similar tunneling service
4. Ensure `ALLOWED_HOSTS` includes your public domain

### "Unsupported file type" Error
**Cause**: The file type is not supported by Office Web Viewer.

**Solution**: Only these formats work:
- Word: `.docx`, `.doc`
- Excel: `.xlsx`, `.xls`  
- PowerPoint: `.pptx`, `.ppt`

### Slow Loading
**Cause**: Large files or slow internet connection.

**Solutions**:
- Microsoft's service may take time for large files
- Consider using Collabora for large documents
- Optimize document file sizes before uploading

## Security Considerations

### ⚠️ Important Security Notes:

1. **Data Privacy**: Documents are sent to Microsoft's servers for rendering
2. **Confidential Data**: Do NOT use for highly confidential documents
3. **Access Control**: Ensure proper Django permissions are in place
4. **Public URLs**: Only make documents public that should be publicly viewable

### Recommended Security Practices:

```python
# In your view
if not document.is_public and not request.user.is_staff:
    messages.error(request, 'Access denied.')
    return redirect('documents:index')
```

## Code Reference

### View Function (`views.py`):
```python
@login_required
def office_web_viewer(request, doc_id):
    """View Office documents using Microsoft Office Web Viewer"""
    document = get_object_or_404(Document, pk=doc_id)
    
    # Build public URL
    document_url = request.build_absolute_uri(document.file.url)
    encoded_url = quote(document_url, safe='')
    
    # Microsoft viewer endpoint
    viewer_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
    
    return render(request, 'documents/office_web_viewer.html', {
        'document': document,
        'viewer_url': viewer_url,
        'can_edit': request.user.is_staff,
    })
```

## Testing

### Local Testing with ngrok:

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. In another terminal, start ngrok:
   ```bash
   ngrok http 8000
   ```

3. Update `settings.py`:
   ```python
   ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-ngrok-url.ngrok.io']
   ```

4. Access your app via the ngrok URL
5. Test the Office Web Viewer with an uploaded document

## Resources

- [Microsoft Office Web Viewer Documentation](https://docs.microsoft.com/en-us/office/dev/add-ins/testing/debug-office-add-ins-on-ipad-and-mac)
- [Office Online Server](https://docs.microsoft.com/en-us/officeonlineserver/office-online-server)

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify document URL accessibility
3. Review Django server logs
4. Check browser developer console

---

**Last Updated**: February 2026  
**Version**: 1.0
