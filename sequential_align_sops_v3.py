
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
    (2, "CONTROL_BOX", ["CONTROL BOX", "VERSION CONTROL", "APPROVED BY"]),
    (3, "DISTRIBUTION_LIST", ["DISTRIBUTION LIST", "COPY NO."]),
    (4, "CHANGE_HISTORY", ["CHANGE HISTORY", "REVISION HISTORY"]),
    (5, "PURPOSE", ["PURPOSE", "POLICY STATEMENT", "OBJECTIVE"]),
    (6, "SCOPE", ["SCOPE", "APPLICABILITY"]),
    (7, "DEFINITIONS", ["DEFINITIONS", "GLOSSARY"]),
    (8, "ROLES_RESPONSIBILITIES", ["ROLES", "RESPONSIBILITY", "RESPONSIBILITIES"]),
    (9, "REQUIRED_MATERIALS", ["MATERIALS", "EQUIPMENT", "MATERIALS REQUIRED", "REAGENTS"]),
    (10, "PROCEDURE", ["PROCEDURE", "METHOD", "OPERATIONAL STEPS", "POLICY PROCEDURES"]),
    (11, "HIGH_ALERT", ["HIGH-ALERT", "CRITICAL MEDICATION"]),
    (12, "SAFETY", ["SAFETY", "PRECAUTIONS", "INFECTION CONTROL"]),
    (13, "RECORDS", ["DOCUMENTATION", "RECORDS", "ARCHIVING"]),
    (14, "REFERENCES", ["REFERENCES", "BIBLIOGRAPHY"])
]

def clean_html_text(text):
    text = text.strip()
    # Remove leading numbering like "1.1 ", "5. ", "10.0 "
    text = re.sub(r'^\d+(\.\d+)*\s*', '', text)
    return text

def get_block_html(block):
    if isinstance(block, Table):
        # Premium Table look
        html = '<div class="table-responsive my-3"><table class="table table-bordered border-primary-subtle shadow-sm"><tbody>'
        for row in block.rows:
            html += '<tr>' + "".join(f'<td class="p-3">{c.text.strip()}</td>' for c in row.cells) + '</tr>'
        html += '</tbody></table></div>'
        return html
    else:
        text = clean_html_text(block.text)
        if not text: return ""
        return f'<p class="mb-3 lead-sm">{text}</p>'

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

def run_alignment_v3():
    doc_obj = HubDocument.objects.get(id=4)
    doc = Document(doc_obj.file.path)
    user = User.objects.filter(is_superuser=True).first()
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Alignment V3: Diagnostic-Driven...")
    SOP.objects.all().delete()

    sops_raw = []
    current_stream = []
    last_sop_idx = -100 # Reset distance

    all_blocks = list(iter_block_items(doc))
    
    # 1. Identification
    for idx, block in enumerate(all_blocks):
        text = ""
        is_table = isinstance(block, Table)
        if is_table:
            text = " ".join(c.text for r in block.rows for c in r.cells).upper()
        else:
            text = block.text.strip().upper()

        # Strict SOP Header: Must be a Table AND contain "MBUYA DORCAS" AND match "MDH-" pattern
        # OR be a very specific paragraph with "MDH-" heading.
        is_split = False
        if is_table and "MBUYA DORCAS" in text and "CODE:" in text:
            is_split = True
        elif not is_table and re.search(r'^MDH-[A-Z]+-\d+\s+', text):
            is_split = True
        
        if is_split and (idx - last_sop_idx > 10):
            if current_stream: sops_raw.append(current_stream)
            current_stream = []
            last_sop_idx = idx
        
        current_stream.append(block)
    
    if current_stream: sops_raw.append(current_stream)

    print(f"Aligning {len(sops_raw)} SOPs...")
    batch = []
    
    for stream in sops_raw:
        sop_data = {i: [] for i in range(1, 15)}
        active_idx = 1
        code = "MDH-XXX-000"
        title = "In-Progress Alignment"

        for b in stream:
            text = ""
            is_table = isinstance(b, Table)
            if is_table:
                text = " ".join(c.text for r in b.rows for c in r.cells).upper()
            else:
                text = b.text.strip().upper()
                if not text: continue

            # Detect section
            for s_idx, _, keywords in SECTIONS_MAP:
                if any(kw in text for kw in keywords) and len(text) < 200:
                    if s_idx >= active_idx: # Sequential progression
                        active_idx = s_idx
                        break
            
            # Special metadata grab from Header Table
            if active_idx == 1:
                # Code
                cm = re.search(r'MDH-[A-Z]+-\d+', " ".join(text.split())) # Collapse spaces
                if cm: code = cm.group(0)
                # Title
                if is_table:
                    cells = [c.text.strip() for r in b.rows for c in r.cells if len(c.text.strip()) > 5]
                    for c in cells:
                        cup = c.upper()
                        if "MBUYA" not in cup and "CODE:" not in cup and "VERSION" not in cup and "MDH-" not in cup:
                            title = c.replace("\n", " ")
                            break

            sop_data[active_idx].append(b)

        # Build Aligned Content
        html = ""
        for s_idx, s_name, _ in SECTIONS_MAP:
            html += f'<h3 class="mt-5 border-start border-4 border-primary ps-3 uppercase text-primary-emphasis">{s_idx}. {s_name.replace("_", " ")}</h3>'
            if sop_data[s_idx]:
                for block in sop_data[s_idx]:
                    html += get_block_html(block)
            else:
                html += '<p class="text-muted p-2 bg-light border-start border-2">N/A - This section was empty in the manual</p>'

        styled_html = f'<div class="sop-standard-markdown">{html}</div>'
        
        prefix = code.split("-")[1] if "-" in code else "ADM"
        MAP = {'FIN': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 'SAF': 'Safety & Infection Control', 'ADM': 'Administrative'}
        cat = cat_objs.get(MAP.get(prefix.upper(), 'Administrative'), cat_objs['Administrative'])

        batch.append(SOP(
            title=f"{code} - {title}"[:200],
            category=cat,
            content=styled_html,
            status="Published",
            version="1.0",
            created_by=user
        ))

    SOP.objects.bulk_create(batch)
    print("Alignment V3 Success!")

if __name__ == "__main__":
    run_alignment_v3()
