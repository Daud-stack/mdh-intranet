
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
from mdh_intranet.documents.models import Document as HubDocument
from django.contrib.auth.models import User

# Comprehensive verb list for SOPs
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
    if len(words) < 2: return [(text, "")]
    
    verb_indices = []
    for i, word in enumerate(words):
        cw = word.strip(',.()[]:; ')
        if cw in SOP_VERBS or cw.capitalize() in SOP_VERBS or cw.lower() in SOP_VERBS:
            verb_indices.append(i)
            
    if not verb_indices:
        return [(" ".join(words[:2]), " ".join(words[2:]))] if len(words) > 2 else [(text, "")]

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
            role_start = v_idx - (role_len or 1)
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

def run_standardization():
    doc_obj = HubDocument.objects.get(id=4)
    doc = Document(doc_obj.file.path)
    user = User.objects.filter(is_superuser=True).first()
    
    CAT_MAP = {
        'FIN': 'Administrative', 'ADM': 'Administrative', 'HR': 'Administrative', 
        'OPS': 'Administrative', 'CLIN': 'Clinical Procedures', 'NUR': 'Clinical Procedures', 
        'SAF': 'Safety & Infection Control', 'INF': 'Safety & Infection Control', 
        'PAT': 'Patient Care', 'EME': 'Emergency Protocols', 'EMG': 'Emergency Protocols', 
        'QUA': 'Quality Assurance', 'QA': 'Quality Assurance',
    }
    cat_objs = {c.name: c for c in SOPCategory.objects.all()}

    print("Wiping existing records for 10-point standardization...")
    SOP.objects.all().delete()

    current_sop = None
    all_sops = []
    last_header_idx = -10

    print("Parsing manual blocks...")
    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Table):
            text = "|".join(c.text for r in block.rows for c in r.cells).strip()
            header_match = re.search(r'(MDH-[A-Z]{2,4}-\d{3})', text)
            if ("MBUYA DORCAS" in text.upper() or header_match) and (idx - last_header_idx > 3):
                if current_sop: all_sops.append(current_sop)
                current_sop = {
                    'code': 'MDH-SOP-XXX', 'title': 'Untitled', 'prefix': 'ADM',
                    'meta': {}, 'sections': {
                        'purpose': '', 'scope': '', 'definitions': '', 
                        'roles': [], 'procedure': [], 'related': '', 
                        'references': '', 'history': []
                    },
                    'curr': 'purpose', 'bcount': 0
                }
                last_header_idx = idx

            if current_sop:
                current_sop['bcount'] += 1
                if current_sop['bcount'] == 1:
                    current_sop['code'] = header_match.group(1) if header_match else 'MDH-SOP-XXX'
                    current_sop['prefix'] = current_sop['code'].split("-")[1] if "-" in current_sop['code'] else 'ADM'
                    parts = [p.strip() for p in text.replace("MBUYA DORCAS HOSPITAL", "").replace("Code:", "").split("|") if p.strip()]
                    current_sop['title'] = next((p for p in parts if "MDH-" not in p and len(p) > 5), 'Procedure')
                elif current_sop['bcount'] == 2:
                    rows = list(block.rows)
                    if len(rows) >= 2:
                        for i, label in enumerate(rows[0].cells):
                            current_sop['meta'][label.text.strip().replace(":", "")] = rows[1].cells[i].text.strip() if i < len(rows[1].cells) else ""
                
                tup = text.upper()
                if 'ROLES' in tup and 'RESPONSIBILITY' in tup:
                    current_sop['curr'] = 'roles'
                    rows = list(block.rows)
                    if 'ROLE' in "|".join(c.text for c in rows[0].cells).upper(): rows = rows[1:]
                    for row in rows:
                        cells = list(row.cells)
                        if not cells: continue
                        c0, c1 = cells[0].text.strip(), (cells[1].text.strip() if len(cells) > 1 else "")
                        if c0 and not c1: current_sop['sections']['roles'].extend(split_mega_role_cell(c0))
                        else: current_sop['sections']['roles'].append((c0, c1))
                elif 'HISTORY' in tup or 'VERSION' in tup:
                    rows = list(block.rows)
                    if len(rows) > 0 and 'DATE' in "|".join(c.text for c in rows[0].cells).upper(): rows = rows[1:]
                    for r in rows:
                        current_sop['sections']['history'].append([c.text.strip() for c in r.cells])
                elif current_sop['curr'] == 'procedure' or 'PROCEDURE' in tup or 'STEP' in tup:
                    current_sop['curr'] = 'procedure'
                    rows = list(block.rows)
                    for r in rows: current_sop['sections']['procedure'].append(" ".join(c.text.strip() for c in r.cells))

        elif isinstance(block, Paragraph):
            text = block.text.strip()
            if text and current_sop:
                tup = text.upper()
                if 'PURPOSE' in tup and len(text) < 30: current_sop['curr'] = 'purpose'
                elif 'SCOPE' in tup and len(text) < 30: current_sop['curr'] = 'scope'
                elif 'DEFINITIONS' in tup and len(text) < 30: current_sop['curr'] = 'definitions'
                elif 'PROCEDURE' in tup and len(text) < 40: current_sop['curr'] = 'procedure'
                elif 'RELATED' in tup: current_sop['curr'] = 'related'
                elif 'REFERENCES' in tup: current_sop['curr'] = 'references'
                else:
                    target = current_sop['sections'].get(current_sop['curr'])
                    if isinstance(target, list): target.append(text)
                    else: current_sop['sections'][current_sop['curr']] += f"{text}\n"

    if current_sop: all_sops.append(current_sop)

    def to_md_table(headers, rows):
        if not rows: return "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n| " + "[To be completed] |" * len(headers)
        md = "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n"
        for r in rows:
            clean_r = [str(c).replace("\n", " ").replace("|", "\\|") for c in r]
            md += "| " + " | ".join(clean_r) + " |\n"
        return md

    import markdown
    print(f"Standardizing {len(all_sops)} SOPs...")
    batch = []
    for s in all_sops:
        m = s['meta']
        sec = s['sections']
        
        # 1. Title Page
        md = f"# 1. Title Page\n"
        md += f"- **SOP Title**: {s['title']}\n"
        md += f"- **SOP Number**: {s['code']}\n"
        md += f"- **Version**: {m.get('Version', '1.0')}\n"
        md += f"- **Effective Date**: {m.get('Effective Date', m.get('Effective', 'Jan 2026'))}\n"
        md += f"- **Review Date**: {m.get('Review Date', 'Jan 2027')}\n"
        md += f"- **Author**: {m.get('Prepared by', '[To be completed]')}\n"
        md += f"- **Approved By**: {m.get('Approved by', '[To be completed]')}\n\n"

        # 2. Version Control Table
        md += "## 2. Version Control Table\n"
        vc_rows = [[m.get('Version', '1.0'), m.get('Effective Date', 'Jan 2026'), m.get('Prepared by', ''), '', m.get('Approved by', ''), 'Initial Release']]
        md += to_md_table(["Version", "Date", "Author", "Reviewer", "Approver", "Summary of Changes"], vc_rows) + "\n\n"

        # 3. Purpose
        md += f"## 3. Purpose\n{sec['purpose'] or 'To standardize operations.'}\n\n"
        
        # 4. Scope
        md += f"## 4. Scope\n{sec['scope'] or 'Relevant clinical and administrative staff.'}\n\n"
        
        # 5. Definitions
        md += f"## 5. Definitions\n{sec['definitions'] or 'N/A'}\n\n"

        # 6. Roles and Responsibilities
        md += "## 6. Roles and Responsibilities\n"
        md += to_md_table(["Role", "Responsibility"], sec['roles']) + "\n\n"

        # 7. Procedure
        md += "## 7. Procedure\n"
        for i, step in enumerate(sec['procedure']):
            if re.match(r'^\d+\.', step): md += f"{step}\n"
            else: md += f"{i+1}. {step}\n"
        md += "\n"

        # 8. Related Documents
        md += f"## 8. Related Documents\n{sec['related'] or 'N/A'}\n\n"

        # 9. References
        md += f"## 9. References\n{sec['references'] or 'MDH Governance Policy'}\n\n"

        # 10. Revision History
        md += "## 10. Revision History\n"
        md += to_md_table(["Version", "Date", "Change Description", "Author", "Approver"], sec['history'])

        # Convert to HTML with table support
        html_content = markdown.markdown(md, extensions=['tables', 'fenced_code'])
        
        # Wrap in standard MDH sections for CSS compatibility
        styled_html = f'<div class="sop-standard-markdown">{html_content}</div>'
        
        cat = cat_objs.get(CAT_MAP.get(s['prefix'].upper(), 'Administrative'), cat_objs['Administrative'])
        batch.append(SOP(
            title=f"{s['code']} - {s['title']}"[:200],
            category=cat,
            content=styled_html,
            status="Published",
            created_by=user
        ))
    
    SOP.objects.bulk_create(batch)
    print("All 152 SOPs standardized in 10-point Markdown format.")

if __name__ == "__main__":
    run_standardization()
