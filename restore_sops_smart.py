
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

# List of common verbs used at the start of responsibility descriptions
SOP_VERBS = {
    'Collect', 'Issue', 'Perform', 'Approve', 'Oversee', 'Ensure', 'Manage', 
    'Handle', 'Record', 'Prepare', 'Review', 'Monitor', 'Maintain', 'Coordinate', 
    'Submit', 'Verify', 'Document', 'Update', 'Sign', 'Check', 'Reconcile', 
    'Inspect', 'Archive', 'Delete', 'Transfer', 'Receive', 'Adhere', 'Follow',
    'Report', 'Escalate', 'Assign', 'Distribute', 'Identify', 'Respond', 'Assist',
    'Authorize', 'Validate', 'Consult', 'Provide', 'Implement', 'Develop'
}

def split_role_responsibility(text):
    """
    Heuristic to split a combined 'Role Responsibility' string.
    Example: 'Cashier Collect payments' -> ('Cashier', 'Collect payments')
    """
    text = text.strip()
    # Strip leading dashes or bullet points
    text = re.sub(r'^[\-\s•]+', '', text)
    
    words = text.split()
    if not words:
        return text, ""
    
    # Heuristic: Find the first word that is a known verb (not at index 0 typically)
    # Most roles are 1-3 words (Cashier, Finance Manager, Senior Nursing Officer)
    limit = min(5, len(words))
    for i in range(1, limit):
        word = words[i].strip(',. ')
        if word in SOP_VERBS or (word.endswith('s') and word[:-1] in SOP_VERBS):
            role = " ".join(words[:i])
            resp = " ".join(words[i:])
            return role, resp
            
    # Fallback: first word as role if no verb found in first 4 words
    if len(words) > 1:
        return words[0], " ".join(words[1:])
    
    return text, ""

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
    doc = Document(file_path)
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    
    CAT_MAP = {
        'FIN': 'Administrative', 'ADM': 'Administrative', 'HR': 'Administrative', 
        'OPS': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 
        'SAF': 'Safety & Infection Control', 'INF': 'Safety & Infection Control', 
        'PAT': 'Patient Care', 'EME': 'Emergency Protocols', 'EMG': 'Emergency Protocols', 
        'QUA': 'Quality Assurance', 'QA': 'Quality Assurance',
    }
    
    for name in set(CAT_MAP.values()):
        SOPCategory.objects.get_or_create(name=name)
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Clearing SOPs...")
    SOP.objects.all().delete()

    current_sop = None
    sops_to_create = []
    last_header_block_index = -5

    print("Parsing document blocks...")
    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            
            # Boundary detection
            is_hospital = "MBUYA DORCAS" in text.upper()
            header_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            
            if (is_hospital or header_match) and (idx - last_header_block_index > 3):
                if current_sop and current_sop['html'].strip():
                    sops_to_create.append(current_sop)
                
                current_sop = {
                    'code': '', 'prefix': 'ADM', 'title': '', 'html': '', 'is_header': True
                }
                last_header_block_index = idx

            if current_sop:
                if header_match and not current_sop['code']:
                    current_sop['code'] = header_match.group(1)
                    current_sop['prefix'] = header_match.group(1).split("-")[1]
                    parts = [p.strip() for p in text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").split("|") if p.strip()]
                    for p in parts:
                        if "MDH-" not in p and len(p) > 5:
                            current_sop['title'] = p
                            break

                # Convert table to HTML
                is_manual_header = idx - last_header_block_index < 5
                bg_class = "bg-light shadow-sm mb-4" if is_manual_header else "my-3"
                current_sop['html'] += f'<div class="table-responsive {bg_class}"><table class="table table-bordered table-sm">'
                
                rows = list(block.rows)
                if rows:
                    first_row_text = "|".join(c.text for c in rows[0].cells).upper()
                    is_role_table = "ROLE" in first_row_text and "RESPONSIBILITY" in first_row_text
                    is_data_table = is_role_table or any(k in first_row_text for k in ['ACTION', 'DATE', 'STEP', 'VERSION', 'COPY'])
                    
                    if is_data_table:
                        current_sop['html'] += '<thead class="table-primary text-white"><tr>'
                        for cell in rows[0].cells:
                            current_sop['html'] += f'<th class="p-2">{cell.text}</th>'
                        current_sop['html'] += '</tr></thead><tbody>'
                        rows = rows[1:]
                    else:
                        current_sop['html'] += '<tbody>'
                    
                    for row in rows:
                        cells = list(row.cells)
                        row_text = "|".join(c.text for c in cells).strip()
                        
                        # Skip pure "separator" rows (dashes only)
                        if re.match(r'^[\-\s]+$', row_text):
                            continue
                        
                        # Apply smart split for Role/Responsibility if squashed
                        if is_role_table and len(cells) >= 1:
                            cell0_text = cells[0].text.strip()
                            cell1_text = cells[1].text.strip() if len(cells) > 1 else ""
                            
                            if cell0_text and not cell1_text:
                                # Content is squashed into first cell
                                role, resp = split_role_responsibility(cell0_text)
                                current_sop['html'] += f'<tr><td class="p-2">{role}</td><td class="p-2">{resp}</td></tr>'
                            else:
                                # Normal split or both cells have content
                                current_sop['html'] += '<tr>'
                                for cell in cells:
                                    current_sop['html'] += f'<td class="p-2">{cell.text}</td>'
                                current_sop['html'] += '</tr>'
                        else:
                            # Standard row rendering
                            current_sop['html'] += '<tr>'
                            for cell in cells:
                                val = cell.text
                                if is_manual_header: val = f'<b>{val}</b>'
                                current_sop['html'] += f'<td class="p-2">{val}</td>'
                            current_sop['html'] += '</tr>'
                    
                    current_sop['html'] += '</tbody></table></div>'
        
        elif isinstance(block, Paragraph):
            text = block.text.strip()
            if text and current_sop:
                if re.match(r'^(\d+\.|[A-Z]\.|Section|PART)\s+', text, re.I):
                    current_sop['html'] += f'<h4 class="mt-4 mb-3 text-primary border-bottom pb-2 fw-bold">{text}</h4>'
                elif text.isupper() and len(text) < 100 and len(text) > 3:
                     current_sop['html'] += f'<h5 class="mt-3 text-secondary fw-bold">{text}</h5>'
                else:
                    current_sop['html'] += f'<p class="mb-2">{text}</p>'

    if current_sop and current_sop['html'].strip():
        sops_to_create.append(current_sop)
    
    print(f"Final extraction count: {len(sops_to_create)} SOPs.")
    batch = []
    for s in sops_to_create:
        title = f"{s['code']} - {s['title']}"[:200] if s['code'] else (s['title'][:200] or "Untitled")
        cat = cat_objs.get(CAT_MAP.get(s['prefix'], 'Administrative'), cat_objs['Administrative'])
        batch.append(SOP(
            title=title or "SOP Procedure",
            category=cat,
            content=s['html'],
            status="Published",
            created_by=user
        ))
    
    SOP.objects.bulk_create(batch)
    print(f"Successfully restored {len(batch)} SOPs with Role/Responsibility splitting.")

if __name__ == "__main__":
    run_import()
