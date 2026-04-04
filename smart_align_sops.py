
import os
import django
import re
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import markdown

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP, SOPCategory
from mdh_intranet.documents.models import Document as HubDocument
from django.contrib.auth.models import User

# Define the target 14 sections
TARGET_SECTIONS = [
    "HEADER_TABLE", "CONTROL_BOX", "DISTRIBUTION_LIST", "CHANGE_HISTORY",
    "PURPOSE", "SCOPE", "DEFINITIONS", "ROLES_RESPONSIBILITIES",
    "REQUIRED_MATERIALS", "PROCEDURE", "HIGH_ALERT", "SAFETY",
    "RECORDS", "REFERENCES"
]

SECTION_MAPPING = {
    'PURPOSE': 'PURPOSE',
    'SCOPE': 'SCOPE',
    'DEFINITIONS': 'DEFINITIONS',
    'POLICY STATEMENT': 'PURPOSE',
    'ROLES': 'ROLES_RESPONSIBILITIES',
    'RESPONSIBILITY': 'ROLES_RESPONSIBILITIES',
    'MATERIALS': 'REQUIRED_MATERIALS',
    'EQUIPMENT': 'REQUIRED_MATERIALS',
    'PROCEDURE': 'PROCEDURE',
    'METHOD': 'PROCEDURE',
    'HIGH-ALERT': 'HIGH_ALERT',
    'SAFETY': 'SAFETY',
    'DOCUMENTS': 'RECORDS',
    'RECORDS': 'RECORDS',
    'REFERENCES': 'REFERENCES',
}

def clean_text(text):
    return text.strip().replace("\n", " ").replace("|", "\\|")

def table_to_md(table):
    md = ""
    rows = []
    for row in table.rows:
        rows.append([clean_text(cell.text) for cell in row.cells])
    if not rows: return ""
    
    header = rows[0]
    md += "| " + " | ".join(header) + " |\n"
    md += "|" + "---|" * len(header) + "\n"
    for r in rows[1:]:
        md += "| " + " | ".join(r) + " |\n"
    return md

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

def run_smart_extraction():
    doc_obj = HubDocument.objects.get(id=4)
    doc = Document(doc_obj.file.path)
    user = User.objects.filter(is_superuser=True).first()
    
    CAT_MAP = {'FIN': 'Administrative', 'ADM': 'Administrative', 'HR': 'Administrative', 'OPS': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 'SAF': 'Safety & Infection Control', 'INF': 'Safety & Infection Control', 'PAT': 'Patient Care', 'EME': 'Emergency Protocols', 'EMG': 'Emergency Protocols', 'QUA': 'Quality Assurance', 'QA': 'Quality Assurance'}
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Clearing for Smart Align build...")
    SOP.objects.all().delete()

    sops = []
    current_sop = None
    last_sop_idx = -10

    print("Scanning blocks...")
    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = " ".join(c.text for r in block.rows for c in r.cells).upper()
            header_match = re.search(r'(MDH-[A-Z]+-\d+)', text)
            if ("MBUYA DORCAS" in text or header_match) and (idx - last_sop_idx > 5):
                if current_sop: sops.append(current_sop)
                current_sop = {
                    'code': 'MDH-SOP-XXX', 'title': 'Untitled',
                    'data': {k: [] for k in TARGET_SECTIONS},
                    'active_section': 'PURPOSE',
                    'table_count': 0
                }
                last_sop_idx = idx
            
            if current_sop:
                current_sop['table_count'] += 1
                md = table_to_md(block)
                if current_sop['table_count'] == 1:
                    current_sop['data']['HEADER_TABLE'].append(md)
                    # Try extract title/code
                    code_m = re.search(r'(MDH-[A-Z]+-\d+)', text)
                    if code_m: current_sop['code'] = code_m.group(1)
                elif current_sop['table_count'] == 2 and ('VERSION' in text or 'CODE' in text):
                    current_sop['data']['CONTROL_BOX'].append(md)
                elif 'HISTORY' in text or 'CHANGE' in text:
                    current_sop['data']['CHANGE_HISTORY'].append(md)
                elif 'DISTRIBUTION' in text:
                    current_sop['data']['DISTRIBUTION_LIST'].append(md)
                elif 'ROLE' in text and 'RESPONSIBILITY' in text:
                    current_sop['data']['ROLES_RESPONSIBILITIES'].append(md)
                else:
                    # Append table to whatever section we are in
                    current_sop['data'][current_sop['active_section']].append(md)

        elif isinstance(block, Paragraph):
            text = block.text.strip()
            if not text: continue
            
            if current_sop:
                # Check for section header
                # Pattern: Number. Title (e.g. 1. Purpose)
                header_match = re.search(r'^(\d+)\.\s*([A-Z\s&/]+)', text.upper())
                if header_match:
                    title = header_match.group(2).strip()
                    # Map title
                    for key, target in SECTION_MAPPING.items():
                        if key in title:
                            current_sop['active_section'] = target
                            break
                
                # If it's a new SOP Title outside of tables (rare but possible)
                if re.search(r'^MDH-[A-Z]+-\d+', text) and len(text) < 100:
                    # This might be a header. If we didn't just start a SOP, start one.
                    pass 

                current_sop['data'][current_sop['active_section']].append(text)

    if current_sop: sops.append(current_sop)

    print(f"Aligning {len(sops)} SOPs to 14-point standard...")
    batch = []
    for s in sops:
        md_content = ""
        
        # 1. Header Table
        if s['data']['HEADER_TABLE']: md_content += s['data']['HEADER_TABLE'][0] + "\n\n"
        else:
            md_content += f"| Department: [To be completed] | SOP Code: {s['code']} |\n| --- | --- |\n| Title: {s['title']} | Version: 1.0 |\n\n"
        
        # 2-14
        section_titles = [
            (2, "CONTROL BOX", "CONTROL_BOX"),
            (3, "DISTRIBUTION LIST", "DISTRIBUTION_LIST"),
            (4, "CHANGE HISTORY", "CHANGE_HISTORY"),
            (5, "PURPOSE", "PURPOSE"),
            (6, "SCOPE", "SCOPE"),
            (7, "DEFINITIONS", "DEFINITIONS"),
            (8, "ROLES & RESPONSIBILITIES", "ROLES_RESPONSIBILITIES"),
            (9, "REQUIRED MATERIALS", "REQUIRED_MATERIALS"),
            (10, "PROCEDURE", "PROCEDURE"),
            (11, "HIGH-ALERT MEDICATION HANDLING", "HIGH_ALERT"),
            (12, "SAFETY PRECAUTIONS", "SAFETY"),
            (13, "DOCUMENTATION & RECORDS", "RECORDS"),
            (14, "REFERENCES", "REFERENCES")
        ]
        
        for num, display, key in section_titles:
            md_content += f"### {num}. {display}\n"
            content_list = s['data'][key]
            if content_list:
                for item in content_list:
                    # If it's a table (starts with |), just append
                    if item.startswith("|"):
                        md_content += item + "\n"
                    else:
                        # If a paragraph, don't duplicate section headers
                        if not re.search(r'^\d+\.\s*' + key[:4], item.upper()):
                            md_content += item + "\n\n"
            else:
                md_content += "N/A\n\n"

        html = markdown.markdown(md_content, extensions=['tables'])
        styled_html = f'<div class="sop-standard-markdown">{html}</div>'
        
        prefix = s['code'].split("-")[1] if "-" in s['code'] else 'ADM'
        cat = cat_objs.get(CAT_MAP.get(prefix.upper(), 'Administrative'), cat_objs['Administrative'])
        
        batch.append(SOP(
            title=f"{s['code']} - {s['title'][:100]}",
            category=cat,
            content=styled_html,
            status="Published",
            created_by=user
        ))

    SOP.objects.bulk_create(batch)
    print("Alignment Complete.")

if __name__ == "__main__":
    run_smart_extraction()
