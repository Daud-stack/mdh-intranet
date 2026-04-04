from django import template
import os

register = template.Library()

@register.filter
def is_office_doc(file_field):
    """
    Returns True if the file field contains a Microsoft Office document
    viewable by Office Web Viewer (.docx, .xlsx, .pptx, etc.)
    """
    if not file_field:
        return False
        
    try:
        filename = file_field.name
        ext = os.path.splitext(filename)[1].lower()
        
        supported_extensions = [
            '.docx', '.doc',
            '.xlsx', '.xls',
            '.pptx', '.ppt'
        ]
        
        return ext in supported_extensions
    except (AttributeError, TypeError):
        return False
