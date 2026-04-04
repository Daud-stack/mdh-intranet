
from docx import Document
import os
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()

from mdh_intranet.sop_manual.models import SOP, SOPCategory
from django.contrib.auth.models import User

file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"

# Mapping of SOP code prefixes to categories
CATEGORY_MAPPING = {
    'CLIN': 'Clinical Procedures',
    'NUR': 'Clinical Procedures',
    'SAF': 'Safety & Infection Control',
    'INF': 'Safety & Infection Control',
    'PAT': 'Patient Care',
    'EME': 'Emergency Protocols',
    'EMG': 'Emergency Protocols',
    'ADM': 'Administrative',
    'FIN': 'Administrative',
    'OPS': 'Administrative',
    'HR': 'Administrative',
    'QUA': 'Quality Assurance',
    'QA': 'Quality Assurance',
}

def categorize_sop(code):
    """Determine category based on code"""
    if code:
        match = re.match(r'MDH-([A-Z]+)-', code)
        if match:
            prefix = match.group(1)
            return CATEGORY_MAPPING.get(prefix, 'Administrative')
    return 'Administrative'

def extract_and_import_sops():
    doc = Document(file_path)
    
    # Build a mapping of SOP codes to their content
    sops_data = {}
    current_code = None
    current_title = None
    current_content = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # Check if this line contains a SOP code
        code_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})\s*[—-]\s*(.+)', text)
        
        if code_match:
            # Save previous SOP if exists
            if current_code and current_content:
                content_text = '\n'.join(current_content)
                if len(content_text) > 50:
                    sops_data[current_code] = {
                        'title': current_title,
                        'content': content_text
                    }
            
            # Start new SOP
            current_code = code_match.group(1)
            current_title = code_match.group(2).strip()
            current_content = []
        elif current_code and text:
            # Add to current SOP content
            current_content.append(text)
   
    # Don't forget last SOP
    if current_code and current_content:
        content_text = '\n'.join(current_content)
        if len(content_text) > 50:
            sops_data[current_code] = {
                'title': current_title,
                'content': content_text
            }
    
    print(f"Extracted {len(sops_data)} SOPs with content\n")
    
    # Show first few
    for i, (code, data) in enumerate(list(sops_data.items())[:10]):
        print(f"{i+1}. {code}: {data['title'][:60]}")
        print(f"   Content length: {len(data['content'])} chars\n")
    
    # Import into database
    user = User.objects.first()
    if not user:
        print("No users found.")
        return
    
    imported_count = 0
    
    for code, data in sops_data.items():
        # Get category
        cat_name = categorize_sop(code)
        category = SOPCategory.objects.filter(name=cat_name).first()
        
        if not category:
            print(f"⚠ Skipping {code}: Category '{cat_name}' not found")
            continue
        
        # Create title
        full_title = f"{code} - {data['title']}"
        if len(full_title) > 200:
            full_title = full_title[:197] + "..."
        
        # Limit content to avoid database issues
        content = data['content']
        if len(content) > 50000:
            content = content[:50000] + "\n\n[Content truncated...]"
        
        # Create SOP
        sop, created = SOP.objects.get_or_create(
            title=full_title,
            defaults={
                'category': category,
                'content': content,
                'version': '1.0',
                'status': 'Published',
                'created_by': user
            }
        )
        
        if created:
            imported_count += 1
            if imported_count <= 10 or imported_count % 20 == 0:
                print(f"✓ {imported_count}. {sop.title[:80]}")
    
    print(f"\n\n{'='*60}")
    print(f"Import Complete!")
    print(f"{'='*60}")
    print(f"Total imported: {imported_count} SOPs")
    print(f"{'='*60}")

if __name__ == '__main__':
    extract_and_import_sops()
