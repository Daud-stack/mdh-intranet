
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

# Comprehensive list of verbs that typically start a responsibility description
SOP_VERBS = {
    'Collect', 'Issue', 'Perform', 'Approve', 'Oversee', 'Ensure', 'Manage', 
    'Handle', 'Record', 'Prepare', 'Review', 'Monitor', 'Maintain', 'Coordinate', 
    'Submit', 'Verify', 'Document', 'Update', 'Sign', 'Check', 'Reconcile', 
    'Inspect', 'Archive', 'Delete', 'Transfer', 'Receive', 'Adhere', 'Follow',
    'Report', 'Escalate', 'Assign', 'Distribute', 'Identify', 'Respond', 'Assist',
    'Authorize', 'Validate', 'Consult', 'Provide', 'Implement', 'Develop', 'Execute'
}

def split_mega_role_cell(text):
    """
    Cleverly splits a single string containing multiple Roles and Responsibilities
    into a list of (Role, Responsibility) tuples.
    """
    text = text.strip()
    # Strip leading markers/dashes
    text = re.sub(r'^[\-\s•]+', '', text)
    
    words = text.split()
    if not words:
        return []
    
    results = []
    current_role_start = 0
    last_verb_idx = -1
    
    i = 0
    while i < len(words):
        word_clean = words[i].strip(',. ')
        # Special case for 'Approve' often appearing as 'Approve.' or similar
        if word_clean in SOP_VERBS or (word_clean.endswith('s') and word_clean[:-1] in SOP_VERBS):
            if last_verb_idx != -1:
                # Identify the start of the next role by looking back for capitalized words
                role_len = 0
                for j in range(i-1, last_verb_idx, -1):
                    # If it's a capitalized word or a common small word in a role (of, and)
                    if words[j][0].isupper() or words[j] in ['of', 'and', '&', 'the']:
                        role_len += 1
                    else:
                        break
                
                if role_len == 0: role_len = 1
                role_start = i - role_len
                
                # Extract previous pair
                role_prev = " ".join(words[current_role_start : last_verb_idx])
                resp_prev = " ".join(words[last_verb_idx : role_start]).strip(',. ')
                if role_prev and resp_prev:
                    results.append((role_prev, resp_prev))
                
                current_role_start = role_start
            
            last_verb_idx = i
        i += 1
        
    # Append the last pair
    if last_verb_idx != -1:
        role = " ".join(words[current_role_start : last_verb_idx])
        resp = " ".join(words[last_verb_idx :]).strip(',. ')
        if role and resp:
            results.append((role, resp))
    elif words:
        # Fallback if no verbs found
        half = len(words) // 2
        results.append((" ".join(words[:half]), " ".join(words[half:])))
        
    return results

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

    print("Clearing database...")
    SOP.objects.all().delete()

    current_sop = None
    sops_to_create = []
    last_header_block_index = -10

    print("Executing extraction...")
    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            
            is_hospital = "MBUYA DORCAS" in text.upper()
            header_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            
            if (is_hospital or header_match) and (idx - last_header_block_index > 3):
                if current_sop and current_sop['html'].strip():
                    sops_to_create.append(current_sop)
                
                current_sop = {'code': '', 'prefix': 'ADM', 'title': '', 'html': ''}
                last_header_block_index = idx

            if current_sop:
                if header_match and not current_sop['code']:
                    current_sop['code'] = header_match.group(1)
                    current_sop['prefix'] = header_match.group(1).split("-")[1]
                    # Title
                    cleaned = text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").strip(" |")
                    t_match = re.search(r'MDH-[A-Z]+-\d+\s*[-–—]\s*(.+)', cleaned)
                    if t_match:
                        current_sop['title'] = t_match.group(1).split("|")[0].strip()
                    else:
                        for p in [p.strip() for p in cleaned.split("|") if p.strip()]:
                            if "MDH-" not in p and len(p) > 5:
                                current_sop['title'] = p; break

                is_manual_header = idx - last_header_block_index < 5
                bg_class = "bg-light shadow-sm mb-4" if is_manual_header else "my-3"
                
                rows = list(block.rows)
                if not rows: continue
                
                first_row_text = "|".join(c.text for c in rows[0].cells).upper()
                is_role_table = "ROLE" in first_row_text and "RESPONSIBILITY" in first_row_text
                is_data_table = is_role_table or any(k in first_row_text for k in ['ACTION', 'DATE', 'STEP', 'VERSION', 'COPY'])
                
                html = f'<div class="table-responsive {bg_class}"><table class="table table-bordered table-sm">'
                
                if is_data_table:
                    html += '<thead class="table-primary text-white"><tr>'
                    for cell in rows[0].cells:
                        html += f'<th class="p-2">{cell.text}</th>'
                    html += '</tr></thead><tbody>'
                    rows = rows[1:]
                else:
                    html += '<tbody>'
                
                for row in rows:
                    cells = list(row.cells)
                    row_text = "|".join(c.text for c in cells).strip()
                    if re.match(r'^[\-\s]+$', row_text): continue
                    
                    if is_role_table and len(cells) >= 1:
                        cell0 = cells[0].text.strip()
                        cell1 = cells[1].text.strip() if len(cells) > 1 else ""
                        
                        if cell0 and not cell1:
                            # MEGA SPLIT
                            pairs = split_mega_role_cell(cell0)
                            for r, re_p in pairs:
                                html += f'<tr><td class="p-2"><b>{r}</b></td><td class="p-2">{re_p}</td></tr>'
                        else:
                            html += '<tr>'
                            for c in cells: html += f'<td class="p-2">{c.text}</td>'
                            html += '</tr>'
                    else:
                        html += '<tr>'
                        for c in cells:
                            val = c.text
                            if is_manual_header: val = f'<b>{val}</b>'
                            html += f'<td class="p-2">{val}</td>'
                        html += '</tr>'
                
                html += '</tbody></table></div>'
                current_sop['html'] += html
        
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
    
    print(f"Extraction finished. committing {len(sops_to_create)} SOPs...")
    to_save = []
    for i, s in enumerate(sops_to_create):
        title = f"{s['code']} - {s['title']}"[:200] if s['code'] else (s['title'][:200] or "Procedure")
        cat = cat_objs.get(CAT_MAP.get(s['prefix'], 'Administrative'), cat_objs['Administrative'])
        to_save.append(SOP(title=title, category=cat, content=s['html'], status="Published", created_by=user))
    
    SOP.objects.bulk_create(to_save)
    print("Restore successful with mega-split capability!")

if __name__ == "__main__":
    run_import()
