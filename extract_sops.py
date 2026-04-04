
from docx import Document
import os
import re
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()

from mdh_intranet.sop_manual.models import SOP, SOPCategory
from django.contrib.auth.models import User

file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"

def extract_sops():
    doc = Document(file_path)
    
    # Strategy: Look for headings that indicate SOP titles
    # Typically formatted as "SOP-XXX: Title" or similar patterns
    
    sops = []
    current_sop = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        if not text:
            continue
            
        # Check if this is a SOP title (usually has SOP code like MDH-XXX-001 or "Standard Operating Procedure")
        # Common patterns: "SOP: ", "SOP-", starts with code like "MDH-"
        is_title = False
        
        # Pattern 1: Lines that start with SOP codes
        if re.match(r'^(MDH-[A-Z]{3}-\d{3}|SOP-\d{3}|SOP\s+\d{3})', text, re.IGNORECASE):
            is_title = True
        
        # Pattern 2: Heading styles
        if para.style and para.style.name:
            if 'Heading 1' in para.style.name or 'Heading 2' in para.style.name:
                # Check if it looks like a SOP title
                if 'SOP' in text.upper() or 'PROCEDURE' in text.upper() or 'PROTOCOL' in text.upper():
                    is_title = True
        
        if is_title:
            # Save previous SOP if exists
            if current_sop and current_sop['content'].strip():
                sops.append(current_sop)
            
            # Start new SOP
            current_sop = {
                'title': text,
                'content': '',
                'code': ''
            }
            
            # Extract code if present
            code_match = re.match(r'^([A-Z]{2,}-[A-Z]{2,}-\d{3})', text)
            if code_match:
                current_sop['code'] = code_match.group(1)
        else:
            # Add to current SOP content
            if current_sop:
                current_sop['content'] += text + '\n\n'
    
    # Don't forget last SOP
    if current_sop and current_sop['content'].strip():
        sops.append(current_sop)
    
    print(f"Found {len(sops)} potential SOPs")
    
    # Print first few for verification
    for i, sop in enumerate(sops[:5]):
        print(f"\n--- SOP {i+1} ---")
        print(f"Title: {sop['title'][:100]}")
        print(f"Code: {sop['code']}")
        print(f"Content length: {len(sop['content'])} chars")
        print(f"First 200 chars: {sop['content'][:200]}")
    
    return sops

if __name__ == '__main__':
    sops = extract_sops()
    
    # Ask for confirmation before importing
    print(f"\n\nReady to import {len(sops)} SOPs into the database.")
    print("This is a dry run. Review the output above.")
