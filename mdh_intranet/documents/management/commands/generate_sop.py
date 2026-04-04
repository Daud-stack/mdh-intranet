from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from mdh_intranet.documents.models import Document, DocumentCategory
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import json
import os
import io
from htmldocx import HtmlToDocx
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate SOP from JSON data file using the system template'
    
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON data file')
        parser.add_argument('--template', type=str, default='documents/sop_template.html', help='Template path')

    def handle(self, *args, **options):
        json_path = options['json_file']
        template_name = options['template']
        
        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f'File not found: {json_path}'))
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.stdout.write(f"Generating SOP: {data.get('sop_title', 'Untitled')}")
            
            # Context prep
            # Handle category name to ID or object
            cat_name = data.get('category', 'Standard Operating Procedures')
            # If plain string passed
            if isinstance(cat_name, str):
                category, _ = DocumentCategory.objects.get_or_create(name=cat_name)
            else:
                category = DocumentCategory.objects.first()
                
            # Defaults
            if 'version_date' not in data:
                data['version_date'] = timezone.now().date()
            if 'effective_date' not in data:
                data['effective_date'] = timezone.now().date()
                
            # Render HTML using Django engine (handles |linebreaks correctly)
            try:
                html_content = render_to_string(template_name, data)
                self.stdout.write("Template rendered successfully.")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Template rendering failed: {e}"))
                return

            # Convert to DOCX
            self.stdout.write("Converting to DOCX...")
            from mdh_intranet.sop_manual.export_utils import preprocess_html_for_docx
            
            html_content = preprocess_html_for_docx(html_content)
            
            new_parser = HtmlToDocx()
            docx = new_parser.parse_html_string(html_content)
            
            buffer = io.BytesIO()
            docx.save(buffer)
            buffer.seek(0)
            
            # Save to Document model
            User = get_user_model()
            # Assign to first superuser or generic
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
            
            doc = Document(
                title=data.get('sop_title', 'Generated SOP'),
                category=category,
                uploaded_by=user,
                description=f"Auto-generated SOP {data.get('sop_code', '')}",
                is_public=False
            )
            
            code = data.get('sop_code', 'SOP').replace('/', '-')
            ver = data.get('version', '1.0')
            filename = f"{code}_v{ver}.docx".replace(' ', '_')
            
            doc.file.save(filename, ContentFile(buffer.getvalue()), save=True)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created document: "{doc.title}" (ID: {doc.pk}). View it in the Documents module.'))
            
        except ImportError:
             self.stderr.write(self.style.ERROR('htmldocx library missing. Install with: pip install htmldocx'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
