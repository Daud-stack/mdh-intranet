
import os
import django
import re
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP, SOPCategory
from django.contrib.auth.models import User

# Standard block iterator to preserve order in the document
def iter_block_items(parent):
    if isinstance(parent, DocType):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("unsupported parent type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def run_import():
    file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"
    print(f"Loading document: {file_path}")
    doc = Document(file_path)
    
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not user:
        print("Error: No user found. Please create a user first.")
        return

    # Category Mapping
    CAT_MAP = {
        'FIN': 'Administrative', 'ADM': 'Administrative', 'HR': 'Administrative', 
        'OPS': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 
        'SAF': 'Safety & Infection Control', 'INF': 'Safety & Infection Control', 
        'PAT': 'Patient Care', 'EME': 'Emergency Protocols', 'EMG': 'Emergency Protocols', 
        'QUA': 'Quality Assurance', 'QA': 'Quality Assurance',
    }
    
    # Ensure categories exist in DB
    for name in set(CAT_MAP.values()):
        SOPCategory.objects.get_or_create(name=name)
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Cleaning existing database SOPs...")
    SOP.objects.all().delete()

    current_sop = None
    sops_to_create = []
    
    print("Beginning extraction loop...")
    for block in iter_block_items(doc):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            
            # Detect a new SOP Header block
            # Logic: Table contains "MBUYA DORCAS" and "Code:" or similar header fields
            is_hospital_header = "MBUYA DORCAS HOSPITAL" in text.upper()
            code_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            
            if is_hospital_header or (code_match and len(text) < 500):
                # New SOP boundary detected
                if current_sop and current_sop['content'].strip():
                    sops_to_create.append(current_sop)
                
                # Start new SOP structure
                current_sop = {'code': '', 'title': '', 'content': '', 'prefix': 'ADM'}
                
                if code_match:
                    current_sop['code'] = code_match.group(1)
                    current_sop['prefix'] = code_match.group(1).split("-")[1]
                
                # Attempt to extract title from the same header table
                # Title often appears after code or hospital name
                cleaned = text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").strip(" |")
                title_match = re.search(r'MDH-[A-Z]+-\d+\s*[-–—]\s*(.+)', cleaned)
                if title_match:
                    current_sop['title'] = title_match.group(1).split("|")[0].strip()
                else:
                    parts = [p.strip() for p in cleaned.split("|") if p.strip()]
                    for p in parts:
                        if "MDH-" not in p and "SOP" not in p.upper() and len(p) > 5:
                            current_sop['title'] = p
                            break
            
            elif current_sop:
                # Add table text as content (useful for internal tables like distribution lists)
                current_sop['content'] += "\n" + text.replace("|", " | ") + "\n\n"
        
        elif isinstance(block, Paragraph):
            text = block.text.strip()
            if text and current_sop:
                # Skip TOC-like lines at the beginning if they contain MDH codes but aren't in tables
                # Since we only start current_sop on a table, this should naturally skip the TOC
                current_sop['content'] += text + "\n\n"

    # Save last SOP
    if current_sop and current_sop['content'].strip():
        sops_to_create.append(current_sop)
    
    print(f"Extracted {len(sops_to_create)} SOPs from document.")
    
    # Save to Database
    to_create = []
    for i, s in enumerate(sops_to_create):
        code = s['code'] or f"SOP-{i:03d}"
        title = s['title'] or "Documented Procedure"
        full_title = f"{code} - {title}"[:200]
        cat = cat_objs.get(CAT_MAP.get(s['prefix'], 'Administrative'), cat_objs['Administrative'])
        
        # Simple content cleanup
        content = re.sub(r'^[ \-—–]+', '', s['content'], flags=re.MULTILINE)
        
        to_create.append(SOP(
            title=full_title,
            category=cat,
            content=content,
            version="1.0",
            status="Published",
            created_by=user
        ))
    
    SOP.objects.bulk_create(to_create)
    print(f"Successfully imported {len(to_create)} SOPs into the database.")

if __name__ == "__main__":
    run_import()
