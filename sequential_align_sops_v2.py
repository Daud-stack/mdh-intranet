
import os
import django
import re
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP, SOPCategory
from mdh_intranet.documents.models import Document as HubDocument
from django.contrib.auth.models import User

# Define the sequence of sections
SECTIONS_MAP = [
    (1, "HEADER_TABLE", ["MBUYA DORCAS", "DEPARTMENT:", "SOP CODE:"]),
    (2, "CONTROL_BOX", ["CONTROL BOX", "VERSION CONTROL"]),
    (3, "DISTRIBUTION_LIST", ["DISTRIBUTION LIST", "COPY NO."]),
    (4, "CHANGE_HISTORY", ["CHANGE HISTORY", "REVISION HISTORY"]),
    (5, "PURPOSE", ["PURPOSE", "POLICY STATEMENT", "OBJECTIVE"]),
    (6, "SCOPE", ["SCOPE", "APPLICABILITY"]),
    (7, "DEFINITIONS", ["DEFINITIONS", "GLOSSARY"]),
    (8, "ROLES_RESPONSIBILITIES", ["ROLES", "RESPONSIBILITY", "RESPONSIBILITIES"]),
    (9, "REQUIRED_MATERIALS", ["MATERIALS", "EQUIPMENT", "MATERIALS REQUIRED"]),
    (10, "PROCEDURE", ["PROCEDURE", "METHOD", "OPERATIONAL STEPS"]),
    (11, "HIGH_ALERT", ["HIGH-ALERT", "CRITICAL MEDICATION"]),
    (12, "SAFETY", ["SAFETY", "PRECAUTIONS", "INFECTION CONTROL"]),
    (13, "RECORDS", ["DOCUMENTATION", "RECORDS", "ARCHIVING"]),
    (14, "REFERENCES", ["REFERENCES", "BIBLIOGRAPHY"])
]

def clean_html_text(text):
    # Remove manual numbering from the doc (e.g. "1.1 ")
    return re.sub(r'^\d+(\.\d+)*\s*', '', text.strip())

def get_block_html(block):
    if isinstance(block, Table):
        html = '<div class="table-responsive my-3"><table class="table table-bordered table-sm"><tbody>'
        for row in block.rows:
            html += '<tr>' + "".join(f'<td class="p-2">{c.text.strip()}</td>' for c in row.cells) + '</tr>'
        html += '</tbody></table></div>'
        return html
    else:
        text = clean_html_text(block.text)
        if not text: return ""
        return f'<p class="mb-2">{text}</p>'

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

def run_alignment_v2():
    doc_obj = HubDocument.objects.get(id=4)
    doc = Document(doc_obj.file.path)
    user = User.objects.filter(is_superuser=True).first()
    
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}
    print("Alignment V2 started...")
    SOP.objects.all().delete()

    sops_raw = []
    current_stream = []
    last_sop_idx = -10

    # 1. Sequential Stream Extraction
    all_blocks = list(iter_block_items(doc))
    for idx, block in enumerate(all_blocks):
        text = ""
        if isinstance(block, Table):
            text = " ".join(c.text for r in block.rows for c in r.cells).upper()
        else:
            text = block.text.strip().upper()

        # New SOP delimiter
        if ("MBUYA DORCAS" in text or "SOP CODE:" in text) and (idx - last_sop_idx > 5):
            if current_stream: sops_raw.append(current_stream)
            current_stream = []
            last_sop_idx = idx
        
        current_stream.append(block)
    
    if current_stream: sops_raw.append(current_stream)

    print(f"Aligning {len(sops_raw)} SOPs...")
    batch = []
    
    for stream in sops_raw:
        sop_data = {i: [] for i in range(1, 15)}
        active_idx = 1 # Start with Header
        sop_code = "MDH-SOP-XXX"
        sop_title = "Untitled SOP"

        # 2. Assign blocks to sections
        for block in stream:
            text = ""
            is_table = isinstance(block, Table)
            if is_table:
                text = " ".join(c.text for r in block.rows for c in r.cells).upper()
            else:
                text = block.text.strip().upper()
                if not text: continue

            # Detect section shifts
            shifted = False
            for s_idx, _, keywords in SECTIONS_MAP:
                # If block matches keywords and is either a table header or a short paragraph
                if any(kw in text for kw in keywords) and (len(text) < 150):
                    # Special check: don't shift to 8 (Roles) if it's just a mention in text
                    if s_idx > active_idx or s_idx == 1: # Usually sequential or restarting
                        active_idx = s_idx
                        shifted = True
                        break
            
            # Special data extraction for Title/Code
            if active_idx == 1:
                # Look for code in header
                if "MDH-" in text:
                    m = re.search(r'MDH-[A_Z0-9\-]+', text)
                    if m: sop_code = m.group(0)
                # Look for Title
                if is_table and len(text) > 20:
                    # In a header table, title is usually the longest cell or contains 'TITLE'
                    cells = [c.text.strip() for r in block.rows for c in r.cells]
                    for c in cells:
                        if len(c) > 10 and "MBUYA" not in c.upper() and "MDH-" not in c.upper():
                            sop_title = c.replace("\n", " ")
        
            sop_data[active_idx].append(block)

        # 3. Assemble HTML
        content_html = ""
        for s_idx, s_name, _ in SECTIONS_MAP:
            # Format title as H3 for our CSS
            display_title = s_name.replace("_", " ")
            content_html += f"<h3>{s_idx}. {display_title}</h3>"
            
            blocks = sop_data[s_idx]
            if blocks:
                for b in blocks:
                    content_html += get_block_html(b)
            else:
                content_html += "<p>N/A</p>"

        final_html = f'<div class="sop-standard-markdown">{content_html}</div>'
        
        # Determine category
        prefix = sop_code.split("-")[1] if "-" in sop_code else "ADM"
        MAP = {'FIN': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 'SAF': 'Safety & Infection Control'}
        cat = cat_objs.get(MAP.get(prefix.upper(), 'Administrative'), cat_objs['Administrative'])

        batch.append(SOP(
            title=f"{sop_code} - {sop_title}"[:200],
            category=cat,
            content=final_html,
            status="Published",
            version="1.0",
            created_by=user
        ))

    SOP.objects.bulk_create(batch)
    print("Alignment V2 Success!")

if __name__ == "__main__":
    run_alignment_v2()
