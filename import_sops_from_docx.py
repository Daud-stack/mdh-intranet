
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
    'ADM': 'Administrative',
    'FIN': 'Administrative',
    'QUA': 'Quality Assurance',
    'HR': 'Administrative',
}

def categorize_sop(title, code):
    """Determine category based on code or title"""
    # Extract prefix from code
    if code:
        match = re.match(r'MDH-([A-Z]+)-', code)
        if match:
            prefix = match.group(1)
            if prefix in CATEGORY_MAPPING:
                return CATEGORY_MAPPING[prefix]
    
    # Fallback to keywords in title
    title_upper = title.upper()
    if any(word in title_upper for word in ['CLINICAL', 'MEDICAL', 'NURSING', 'PATIENT CARE']):
        return 'Clinical Procedures'
    elif any(word in title_upper for word in ['SAFETY', 'INFECTION', 'HYGIENE']):
        return 'Safety & Infection Control'
    elif any(word in title_upper for word in ['EMERGENCY', 'CRISIS']):
        return 'Emergency Protocols'
    elif any(word in title_upper for word in ['ADMIN', 'FINANCE', 'HR', 'BILLING']):
        return 'Administrative'
    elif any(word in title_upper for word in ['QUALITY', 'AUDIT']):
        return 'Quality Assurance'
    
    return 'Administrative'  # Default

def extract_and_import_sops():
    doc = Document(file_path)
    
    # Look for lines that match SOP codes
    sops = []
    current_sop = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        if not text:
            continue
        
        # Check if this line contains a SOP code at the start
        code_match = re.match(r'^(MDH-[A-Z]{2,4}-\d{3})\s*[—-]\s*(.+)', text)
        
        if code_match:
            # This is a SOP title
            if current_sop and len(current_sop['content']) > 100:  # Only save if has content
                sops.append(current_sop)
            
            sop_code = code_match.group(1)
            sop_title = code_match.group(2).strip()
            
            current_sop = {
                'code': sop_code,
                'title': sop_title,
                'content': '',
                'full_title': text
            }
        else:
            # Add to content
            if current_sop:
                current_sop['content'] += text + '\n\n'
    
    # Last SOP
    if current_sop and len(current_sop['content']) > 100:
        sops.append(current_sop)
    
    print(f"Extracted {len(sops)} SOPs from document\n")
    
    # Show samples
    for i, sop in enumerate(sops[:10]):
        print(f"{i+1}. {sop['code']}: {sop['title'][:60]}")
        print(f"   Content: {len(sop['content'])} chars")
        print(f"   Category: {categorize_sop(sop['title'], sop['code'])}\n")
    
    # Import into database
    user = User.objects.first()  # Use first user as creator
    if not user:
        print("No users found. Please create a user first.")
        return
    
    imported_count = 0
    for sop_data in sops:
        # Get category
        cat_name = categorize_sop(sop_data['title'], sop_data['code'])
        category = SOPCategory.objects.filter(name=cat_name).first()
        
        if not category:
            print(f"Warning: Category '{cat_name}' not found, skipping {sop_data['code']}")
            continue
        
        # Create SOP
        sop, created = SOP.objects.get_or_create(
            title=f"{sop_data['code']} - {sop_data['title'][:150]}",  # Limit title length
            defaults={
                'category': category,
                'content': sop_data['content'],
                'version': '1.0',
                'status': 'Published',
                'created_by': user
            }
        )
        
        if created:
            imported_count += 1
            if imported_count <= 5:
                print(f"✓ Imported: {sop.title[:80]}")
    
    print(f"\n\nTotal imported: {imported_count} SOPs")
    print("Import complete!")

if __name__ == '__main__':
    extract_and_import_sops()
