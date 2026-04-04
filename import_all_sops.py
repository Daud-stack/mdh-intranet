
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

def split_into_sections(text, code_to_find):
    """Find the section for a specific SOP code"""
    lines = text.split('\n')
    
    # Find where this SOP starts
    start_idx = None
    for i, line in enumerate(lines):
        if code_to_find in line:
            start_idx = i
            break
    
    if start_idx is None:
        return None, None
    
    # Find where next SOP starts (next MDH code)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if re.search(r'MDH-[A-Z]{2,4}-\d{3}', lines[i]) and not code_to_find in lines[i]:
            end_idx = i
            break
    
    # Get title (the line with the code)
    title_line = lines[start_idx].strip()
    
    # Extract title after the code
    title_match = re.search(r'MDH-[A-Z]{2,4}-\d{3}\s*[—-]\s*(.+)', title_line)
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = title_line.replace(code_to_find, '').strip(' —-')
    
    # Get content
    content_lines = lines[start_idx+1:end_idx]
    content = '\n'.join(content_lines).strip()
    
    return title, content

def extract_and_import_sops():
    doc = Document(file_path)
    
    # Get all text as one string for easier splitting
    all_text = '\n'.join([p.text for p in doc.paragraphs])
    
    # Find all unique MDH codes
    all_codes = re.findall(r'(MDH-[A-Z]{2,4}-\d{3})', all_text)
    unique_codes = list(dict.fromkeys(all_codes))  # Preserve order, remove duplicates
    
    print(f"Found {len(unique_codes)} unique SOP codes\n")
    
    user = User.objects.first()
    if not user:
        print("No users found. Create a user first.")
        return
    
    imported_count = 0
    skipped_count = 0
    
    for code in unique_codes:
        title, content = split_into_sections(all_text, code)
        
        if not title or not content or len(content) < 50:
            print(f"⚠ Skipping {code}: insufficient content")
            skipped_count += 1
            continue
        
        # Get category
        cat_name = categorize_sop(code)
        category = SOPCategory.objects.filter(name=cat_name).first()
        
        if not category:
            print(f"⚠ Skipping {code}: Category '{cat_name}' not found")
            skipped_count += 1
            continue
        
        # Truncate title if too long
        full_title = f"{code} - {title}"
        if len(full_title) > 200:
            full_title = full_title[:197] + "..."
        
        # Create SOP
        sop, created = SOP.objects.get_or_create(
            title=full_title,
            defaults={
                'category': category,
                'content': content[:10000],  # Limit content length if needed
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
    print(f"Skipped: {skipped_count} SOPs")
    print(f"{'='*60}")

if __name__ == '__main__':
    extract_and_import_sops()
