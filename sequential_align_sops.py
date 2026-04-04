
import os
import django
import re
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
import markdown

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP, SOPCategory
from mdh_intranet.documents.models import Document as HubDocument
from django.contrib.auth.models import User

# Section anchors with their target 14-point index
ANCHORS = [
    (1, ["MBUYA DORCAS", "DEPARTMENT:", "SOP CODE:"]), # Header
    (2, ["CONTROL BOX", "VERSION CONTROL", "APPROVED BY"]), 
    (3, ["DISTRIBUTION LIST", "COPY NO."]),
    (4, ["CHANGE HISTORY", "REVISION HISTORY"]),
    (5, ["PURPOSE", "POLICY STATEMENT", "OBJECTIVE"]),
    (6, ["SCOPE", "APPLICABILITY"]),
    (7, ["DEFINITIONS", "GLOSSARY"]),
    (8, ["ROLES", "RESPONSIBILITY", "RESPONSIBILITIES"]),
    (9, ["MATERIALS", "EQUIPMENT", "REAGENTS"]),
    (10, ["PROCEDURE", "METHOD", "STEPS"]),
    (11, ["HIGH-ALERT", "CRITICAL MEDICATION"]),
    (12, ["SAFETY", "PRECAUTIONS", "INFECTION CONTROL"]),
    (13, ["DOCUMENTATION", "RECORDS", "ARCHIVING"]),
    (14, ["REFERENCES", "BIBLIOGRAPHY"])
]

def get_block_html(block):
    if isinstance(block, Table):
        html = '<div class="table-responsive my-3"><table class="table table-bordered table-sm"><tbody>'
        for row in block.rows:
            html += '<tr>' + "".join(f'<td class="p-2">{c.text.strip()}</td>' for c in row.cells) + '</tr>'
        html += '</tbody></table></div>'
        return html
    else:
        text = block.text.strip()
        if not text: return ""
        # Clean up existing numbering if it conflicts
        text = re.sub(r'^\d+\.?\s*', '', text)
        return f'<p class="mb-2">{text}</p>'

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

def run_alignment():
    doc_obj = HubDocument.objects.get(id=4)
    doc = Document(doc_obj.file.path)
    user = User.objects.filter(is_superuser=True).first()
    
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}
    print("Alignment started...")
    SOP.objects.all().delete()

    sops_raw = []
    current_blocks = []
    last_sop_idx = -10

    # Phase 1: Split into raw SOP block streams
    for idx, block in enumerate(iter_block_items(doc)):
        text = ""
        if isinstance(block, Table):
            text = " ".join(c.text for r in block.rows for c in r.cells).upper()
        else:
            text = block.text.strip().upper()

        is_header = ("MBUYA DORCAS" in text or re.search(r'MDH-[A-Z]+-\d+', text)) and len(text) < 200
        
        if is_header and (idx - last_sop_idx > 5):
            if current_blocks: sops_raw.append(current_blocks)
            current_blocks = []
            last_sop_idx = idx
        
        current_blocks.append(block)
    
    if current_blocks: sops_raw.append(current_blocks)

    print(f"Processing {len(sops_raw)} SOPs...")
    batch = []
    
    for stream in sops_raw:
        # Phase 2: Map blocks to the 14 sections
        final_sections = {i: [] for i in range(1, 15)}
        active_idx = 5 # Default to Purpose if not sure
        sop_code = "MDH-SOP-XXX"
        sop_title = "Untitled"

        for b in stream:
            text = ""
            if isinstance(b, Table):
                text = " ".join(c.text for r in b.rows for c in r.cells).upper()
            else:
                text = b.text.strip().upper()
            
            # Identify section transitions
            found_new = False
            for idx, keywords in ANCHORS:
                if any(kw in text for kw in keywords) and (len(text) < 100 or isinstance(b, Table)):
                    active_idx = idx
                    found_new = True
                    break
            
            # Special case for first Table (Header)
            if sop_code == "MDH-SOP-XXX":
                m = re.search(r'MDH-[A-Z]+-\d+', text)
                if m: sop_code = m.group(0)
            
            final_sections[active_idx].append(b)

        # Phase 3: Build HTML
        full_html = ""
        section_titles = [
            "HEADER TABLE", "CONTROL BOX", "DISTRIBUTION LIST", "CHANGE HISTORY",
            "PURPOSE", "SCOPE", "DEFINITIONS", "ROLES & RESPONSIBILITIES",
            "REQUIRED MATERIALS", "PROCEDURE", "HIGH-ALERT MEDICATION HANDLING",
            "SAFETY PRECAUTIONS", "DOCUMENTATION & RECORDS", "REFERENCES"
        ]

        for i in range(1, 15):
            title = section_titles[i-1]
            full_html += f"<h3>{i}. {title}</h3>"
            if final_sections[i]:
                for b in final_sections[i]:
                    full_html += get_block_html(b)
            else:
                full_html += "<p>N/A</p>"

        # Final Cleanup
        styled_html = f'<div class="sop-standard-markdown">{full_html}</div>'
        
        prefix = sop_code.split("-")[1] if "-" in sop_code else "ADM"
        CAT_MAP = {'FIN': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 'SAF': 'Safety & Infection Control'}
        cat = cat_objs.get(CAT_MAP.get(prefix.upper(), 'Administrative'), cat_objs['Administrative'])

        batch.append(SOP(
            title=f"{sop_code} - Alignment Pass", # We'll fix title later
            category=cat,
            content=styled_html,
            status="Published",
            created_by=user
        ))

    SOP.objects.bulk_create(batch)
    print("Success: All SOPs aligned sequentially.")

if __name__ == "__main__":
    run_alignment()
