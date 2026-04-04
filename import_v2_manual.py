
import os
import django
import re
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import glob

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
    'Sign-off', 'Assess', 'Evaluate', 'Notify', 'Track', 'Direct', 'Supervise', 'Administer'
}

def split_mega_role_cell(text):
    text = text.strip()
    text = re.sub(r'^[\-\+\s•=_]+', '', text)
    words = text.split()
    if not words: return []
    verb_indices = []
    for i, word in enumerate(words):
        clean_word = word.strip(',.()[]:; ')
        if clean_word in SOP_VERBS or (clean_word.capitalize() in SOP_VERBS) or (clean_word.lower() in SOP_VERBS):
            verb_indices.append(i)
    if not verb_indices:
        if len(words) > 1: return [(" ".join(words[:2]), " ".join(words[2:]))]
        return [(text, "")]
    results = []
    for idx_in_list, v_idx in enumerate(verb_indices):
        if idx_in_list == 0:
            role_start = 0
        else:
            role_len = 0
            prev_v_idx = verb_indices[idx_in_list - 1]
            for j in range(v_idx - 1, max(prev_v_idx, v_idx - 7), -1):
                if words[j][0].isupper() or words[j].lower() in ['of', 'and', 'the', '&']:
                    role_len += 1
                else: break
            if role_len == 0: role_len = 1
            role_start = v_idx - role_len
            prev_role, _ = results[-1]
            prev_resp = " ".join(words[prev_v_idx : role_start]).strip(',. ')
            results[-1] = (prev_role, prev_resp)
        role = " ".join(words[role_start : v_idx]).strip(': ')
        results.append((role, ""))
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
    file_path = r"C:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Updated_V2.docx"
    print(f"Opening: {file_path}")
    doc = Document(file_path)
    user = User.objects.filter(is_superuser=True).first()
    
    CAT_MAP = {'FIN': 'Administrative', 'ADM': 'Administrative', 'HR': 'Administrative', 'OPS': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 'SAF': 'Safety & Infection Control', 'INF': 'Safety & Infection Control', 'PAT': 'Patient Care', 'EME': 'Emergency Protocols', 'EMG': 'Emergency Protocols', 'QUA': 'Quality Assurance', 'QA': 'Quality Assurance'}
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Clearing database...")
    SOP.objects.all().delete()

    current_sop = None
    sops_data = []
    last_header_idx = -10

    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            header_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            is_hospital = "MBUYA DORCAS" in text.upper()
            if (is_hospital or header_match) and (idx - last_header_idx > 3):
                if current_sop: sops_data.append(current_sop)
                current_sop = {'code': '', 'title': '', 'metadata': {}, 'sections': {'purpose': '', 'scope': '', 'definitions': '', 'roles_html': '', 'procedure_html': '', 'related': '', 'references': '', 'history_html': '', 'control_html': ''}, 'current_section': 'purpose', 'block_count_in_sop': 0}
                last_header_idx = idx
            if current_sop:
                current_sop['block_count_in_sop'] += 1
                b_idx = current_sop['block_count_in_sop']
                if b_idx == 1:
                    current_sop['code'] = header_match.group(1) if header_match else 'MDH-SOP-XXX'
                    current_sop['prefix'] = current_sop['code'].split("-")[1] if "-" in current_sop['code'] else 'ADM'
                    parts = [p.strip() for p in text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").split("|") if p.strip()]
                    current_sop['title'] = next((p for p in parts if "MDH-" not in p and len(p) > 5), 'Untitled')
                elif b_idx == 2:
                    rows = list(block.rows)
                    if len(rows) >= 2:
                        for i, label in enumerate(rows[0].cells):
                            current_sop['metadata'][label.text.strip().replace(":", "")] = rows[1].cells[i].text.strip() if i < len(rows[1].cells) else ""
                
                text_up = text.upper()
                if 'ROLES' in text_up and 'RESPONSIBILITY' in text_up:
                    current_sop['current_section'] = 'roles'
                    html = '<div class="table-responsive my-3"><table class="table table-bordered"><thead class="table-primary text-white"><tr><th>Role</th><th>Responsibility</th></tr></thead><tbody>'
                    rows = list(block.rows)
                    if 'ROLE' in "|".join(c.text for c in rows[0].cells).upper(): rows = rows[1:]
                    for row in rows:
                        cells = list(row.cells)
                        if not cells: continue
                        c0, c1 = cells[0].text.strip(), (cells[1].text.strip() if len(cells) > 1 else "")
                        if c0 and not c1:
                            for r, resp in split_mega_role_cell(c0): html += f'<tr><td class="bg-light fw-bold" style="width:30%">{r}</td><td>{resp}</td></tr>'
                        else: html += f'<tr><td class="bg-light fw-bold" style="width:30%">{c0}</td><td>{c1}</td></tr>'
                    html += '</tbody></table></div>'
                    current_sop['sections']['roles_html'] = html
                elif 'HISTORY' in text_up or 'VERSION' in text_up:
                    html = '<div class="table-responsive my-3"><table class="table table-bordered table-sm"><tbody>'
                    for row in block.rows: html += '<tr>' + "".join(f'<td class="p-2">{c.text}</td>' for c in row.cells) + '</tr>'
                    html += '</tbody></table></div>'
                    current_sop['sections']['history_html'] = html
                else:
                    html = '<div class="table-responsive my-3"><table class="table table-bordered table-sm"><tbody>'
                    for row in block.rows: html += '<tr>' + "".join(f'<td class="p-2">{c.text}</td>' for c in row.cells) + '</tr>'
                    html += '</tbody></table></div>'
                    current_sop['sections']['procedure_html'] += html

        elif isinstance(block, Paragraph):
            text = block.text.strip()
            if text and current_sop:
                text_up = text.upper()
                if 'PURPOSE' in text_up and len(text) < 30: current_sop['current_section'] = 'purpose'
                elif 'SCOPE' in text_up and len(text) < 30: current_sop['current_section'] = 'scope'
                elif 'DEFINITIONS' in text_up and len(text) < 30: current_sop['current_section'] = 'definitions'
                elif ('PROCEDURE' in text_up or 'POLICY' in text_up) and len(text) < 40: current_sop['current_section'] = 'procedure'
                elif 'RELATED' in text_up: current_sop['current_section'] = 'related'
                elif 'REFERENCES' in text_up: current_sop['current_section'] = 'references'
                
                if current_sop['current_section'] == 'procedure':
                    if re.match(r'^\d+\.', text):
                        parts = text.split(".", 1)
                        current_sop['sections']['procedure_html'] += f'<div class="mb-3 d-flex"><span class="fw-bold me-2">{parts[0]}.</span><span>{parts[1].strip() if len(parts)>1 else ""}</span></div>'
                    else: current_sop['sections']['procedure_html'] += f'<p class="mb-2">{text}</p>'
                else:
                    sec = current_sop['current_section']
                    if sec in current_sop['sections']: current_sop['sections'][sec] += f'<p class="mb-2">{text}</p>'
                    else: current_sop['sections']['procedure_html'] += f'<p class="mb-2">{text}</p>'

    if current_sop: sops_data.append(current_sop)

    def assemble_html(s):
        m = s['metadata']
        control_box = f"""<div class="sop-control-box p-4 border rounded bg-white shadow-sm mb-5"><div class="row align-items-center mb-4"><div class="col-8"><h2 class="fw-bold text-primary mb-0">{s['title']}</h2><p class="text-muted fs-5">{s['code']}</p></div><div class="col-4 text-end"><div class="fw-bold fs-4 text-primary">MDH</div><div class="small fw-bold">Mbuya Dorcas Hospital</div></div></div><div class="row g-0 border rounded overflow-hidden"><div class="col-md-4 border-end p-3 bg-light"><div class="small text-muted text-uppercase fw-bold">Effective Date</div><div class="fs-5">{m.get('Effective Date', m.get('Effective', 'Jan 2026'))}</div></div><div class="col-md-4 border-end p-3 bg-light"><div class="small text-muted text-uppercase fw-bold">Review Date</div><div class="fs-5">{m.get('Review Date', 'Jan 2027')}</div></div><div class="col-md-4 p-3 bg-light"><div class="small text-muted text-uppercase fw-bold">Version</div><div class="fs-5">{m.get('Version', '1.0')}</div></div></div><div class="row g-0 border rounded overflow-hidden mt-3"><div class="col-md-6 border-end p-3"><div class="small text-muted text-uppercase fw-bold">Prepared By</div><div>{m.get('Prepared by', 'Quality Office')}</div></div><div class="col-md-6 p-3"><div class="small text-muted text-uppercase fw-bold">Approved By</div><div>{m.get('Approved by', 'Hospital Management Board')}</div></div></div></div>"""
        sections_html = ""
        structure = [("3. Purpose", s['sections']['purpose'] or "To standardize operational clinical procedures."), ("4. Scope", s['sections']['scope'] or "All relevant clinical and administrative staff."), ("5. Definitions", s['sections']['definitions'] or "N/A"), ("6. Roles and Responsibilities", s['sections']['roles_html']), ("7. Procedure", s['sections']['procedure_html']), ("8. Related Documents", s['sections']['related'] or "N/A"), ("9. References", s['sections']['references'] or "National Health Guidelines"), ("10. Revision History", s['sections']['history_html'])]
        for title, content in structure:
            if content: sections_html += f"""<div class="sop-section mb-5"><h4 class="fw-bold text-dark border-bottom pb-2 mb-3 mt-4" style="letter-spacing: 0.1rem;">{title}</h4><div class="sop-section-content ps-2">{content}</div></div>"""
        return control_box + sections_html

    print(f"Applying structure to {len(sops_data)} SOPs...")
    batch = []
    for s in sops_data:
        prefix = s['prefix'].upper()
        cat = cat_objs.get(CAT_MAP.get(prefix, 'Administrative'), cat_objs['Administrative'])
        batch.append(SOP(title=f"{s['code']} - {s['title']}"[:200], category=cat, content=assemble_html(s), version=s['metadata'].get('Version', '1.0'), status="Published", created_by=user))
    SOP.objects.bulk_create(batch)
    print("FINISHED.")

if __name__ == "__main__":
    run_import()
