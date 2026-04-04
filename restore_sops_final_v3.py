
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

# Extensive list of verbs that typically start a responsibility description
SOP_VERBS = {
    'Collect', 'Issue', 'Perform', 'Approve', 'Oversee', 'Ensure', 'Manage', 
    'Handle', 'Record', 'Prepare', 'Review', 'Monitor', 'Maintain', 'Coordinate', 
    'Submit', 'Verify', 'Document', 'Update', 'Sign', 'Check', 'Reconcile', 
    'Inspect', 'Archive', 'Delete', 'Transfer', 'Receive', 'Adhere', 'Follow',
    'Report', 'Escalate', 'Assign', 'Distribute', 'Identify', 'Respond', 'Assist',
    'Authorize', 'Validate', 'Consult', 'Provide', 'Implement', 'Develop', 'Execute',
    'Sign-off', 'Assess', 'Evaluate', 'Notify', 'Track', 'Verify', 'Prepare', 'Maintain'
}

def split_mega_role_cell(text):
    text = text.strip()
    text = re.sub(r'^[\-\+\s•=_]+', '', text)
    
    words = text.split()
    if not words: return []
    
    verb_indices = []
    for i, word in enumerate(words):
        clean_word = word.strip(',.()[]:; ')
        # Check against verbs (capitalized or small)
        if clean_word in SOP_VERBS or (clean_word.capitalize() in SOP_VERBS) or (clean_word.endswith('s') and clean_word[:-1].capitalize() in SOP_VERBS):
            verb_indices.append(i)
            
    if not verb_indices:
        if len(words) > 2: return [(" ".join(words[:2]), " ".join(words[2:]))]
        return [(text, "")]

    results = []
    for idx_in_list, v_idx in enumerate(verb_indices):
        if idx_in_list == 0:
            role_start = 0
        else:
            role_len = 0
            prev_v_idx = verb_indices[idx_in_list - 1]
            # Look back for role start (capitalized words)
            # Roles can be up to 6 words long
            for j in range(v_idx - 1, max(prev_v_idx, v_idx - 7), -1):
                if words[j][0].isupper() or words[j].lower() in ['of', 'and', 'the', '&']:
                    role_len += 1
                else: break
            if role_len == 0: role_len = 1
            role_start = v_idx - role_len
            
            # Update previous responsibility
            prev_role, _ = results[-1]
            prev_resp = " ".join(words[prev_v_idx : role_start]).strip(',. ')
            results[-1] = (prev_role, prev_resp)
            
        role = " ".join(words[role_start : v_idx]).strip(': ')
        results.append((role, ""))

    # Last pair
    last_v_idx = verb_indices[-1]
    final_role, _ = results[-1]
    final_resp = " ".join(words[last_v_idx:]).strip(',. ')
    results[-1] = (final_role, final_resp)
    
    return results

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

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

    SOP.objects.all().delete()
    print("Beginning extraction...")
    
    current_sop = None
    sops_to_create = []
    last_header_idx = -10

    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            is_hospital = "MBUYA DORCAS" in text.upper()
            header_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            
            if (is_hospital or header_match) and (idx - last_header_idx > 3):
                if current_sop: sops_to_create.append(current_sop)
                current_sop = {'code': '', 'prefix': 'ADM', 'title': '', 'html': ''}
                last_header_idx = idx

            if current_sop:
                if header_match and not current_sop['code']:
                    current_sop['code'] = header_match.group(1); current_sop['prefix'] = header_match.group(1).split("-")[1]
                    cl = text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").strip(" |")
                    tm = re.search(r'MDH-[A-Z]+-\d+\s*[-–—]\s*(.+)', cl)
                    if tm: current_sop['title'] = tm.group(1).split("|")[0].strip()
                    else:
                        for p in [p.strip() for p in cl.split("|") if p.strip()]:
                            if "MDH-" not in p and len(p) > 5: current_sop['title'] = p; break

                is_manual_header = idx - last_header_idx < 5
                rows = list(block.rows)
                if not rows: continue
                fr_text = "|".join(c.text for c in rows[0].cells).upper()
                is_role_table = any(k in fr_text for k in ['ROLE', 'RESPONSIBILITY']) 
                is_data_table = is_role_table or any(k in fr_text for k in ['ACTION', 'DATE', 'STEP', 'VERSION', 'COPY'])
                
                html = f'<div class="table-responsive {"bg-light mb-4 shadow-sm" if is_manual_header else "my-3"}"><table class="table table-bordered table-sm">'
                if is_data_table:
                    html += '<thead class="table-primary text-white"><tr>'
                    for c in rows[0].cells: html += f'<th class="p-2">{c.text}</th>'
                    html += '</tr></thead><tbody>'; rows = rows[1:]
                else: html += '<tbody>'
                
                for row in rows:
                    cells = list(row.cells)
                    rt = "|".join(c.text for c in cells).strip()
                    if re.match(r'^[\-\s•=_]+$', rt): continue
                    
                    if is_role_table and len(cells) >= 1:
                        c0 = cells[0].text.strip()
                        c1 = cells[1].text.strip() if len(cells) > 1 else ""
                        if c0 and not c1:
                            pairs = split_mega_role_cell(c0)
                            if len(pairs) > 1: print(f"  Split {len(pairs)} roles in a row")
                            for r, re_p in pairs:
                                html += f'<tr><td class="p-2 bg-light"><b>{r}</b></td><td class="p-2">{re_p}</td></tr>'
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
                html += '</tbody></table></div>'; current_sop['html'] += html
        
        elif isinstance(block, Paragraph) and current_sop:
            text = block.text.strip()
            if text:
                if re.match(r'^(\d+\.|[A-Z]\.|Section|PART)\s+', text, re.I):
                    current_sop['html'] += f'<h4 class="mt-4 mb-3 text-primary border-bottom pb-2 fw-bold">{text}</h4>'
                elif text.isupper() and len(text) < 100 and len(text) > 3:
                     current_sop['html'] += f'<h5 class="mt-3 text-secondary fw-bold small text-uppercase">{text}</h5>'
                else: current_sop['html'] += f'<p class="mb-2">{text}</p>'

    if current_sop: sops_to_create.append(current_sop)
    to_save = []
    for s in sops_to_create:
        title = f"{s['code']} - {s['title']}"[:200] if s['code'] else s['title'][:200]
        cat = cat_objs.get(CAT_MAP.get(s['prefix'], 'Administrative'), cat_objs['Administrative'])
        to_save.append(SOP(title=title, category=cat, content=s['html'], status="Published", created_by=user))
    SOP.objects.bulk_create(to_save)
    print("Done! Check Roles tables.")

if __name__ == "__main__":
    run_import()
