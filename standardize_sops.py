
import os
import django
import re
from bs4 import BeautifulSoup

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP, SOPCategory
from django.utils import timezone

def clean_html_content(content):
    """Parses raw content and extracts logical sections."""
    soup = BeautifulSoup(content, 'html.parser')
    sections = {
        'purpose': '',
        'scope': '',
        'definitions': '',
        'roles': '',
        'procedure': '',
        'related': '',
        'references': '',
        'revision': '',
        'version_control': ''
    }
    
    # 1. Extract Roles Table
    roles_header = soup.find(lambda t: t.name in ['h4', 'h5'] and 'ROLES' in t.text.upper())
    if roles_header:
        table = roles_header.find_next('table')
        if table:
            sections['roles'] = str(table)
            table.decompose() # Don't include it in general procedure search
        roles_header.decompose()

    # 2. Extract Version/Revision Tables
    rev_header = soup.find(lambda t: t.name in ['h4', 'h5'] and ('REVISION' in t.text.upper() or 'VERSION' in t.text.upper()))
    if rev_header:
        table = rev_header.find_next('table')
        if table:
            sections['revision'] = str(table)
            sections['version_control'] = str(table)
            table.decompose()
        rev_header.decompose()

    # 3. Use Regex to find standard sections by their number/name
    # We'll split the remaining text by headings
    current_section = 'procedure'
    for element in soup.find_all(['h4', 'h5', 'p', 'div']):
        text = element.text.strip().upper()
        
        if 'PURPOSE' in text and len(text) < 30:
            current_section = 'purpose'
            continue
        elif 'SCOPE' in text and len(text) < 30:
            current_section = 'scope'
            continue
        elif 'DEFINITIONS' in text and len(text) < 30:
            current_section = 'definitions'
            continue
        elif ('PROCEDURE' in text or 'POLICY' in text) and len(text) < 40:
            current_section = 'procedure'
            continue
        elif 'RELATED' in text and len(text) < 50:
            current_section = 'related'
            continue
        elif 'REFERENCES' in text and len(text) < 30:
            current_section = 'references'
            continue

        inner_html = str(element)
        if current_section in sections:
            sections[current_section] += inner_html
            
    return sections

def format_sop(sop):
    sections = clean_html_content(sop.content)
    
    # Extract SOP Number from Title (e.g., MDH-FIN-001)
    match = re.search(r'MDH-[A-Z]+-\d+', sop.title)
    sop_number = match.group(0) if match else "MDH-SOP-XXX"
    sop_title_clean = sop.title.replace(sop_number, "").strip(" -")
    
    # Constructing the New Standard Structure
    html = f"""
    <!-- 1. Title Page -->
    <div class="sop-title-page mb-5 p-4 border rounded bg-white shadow-sm">
        <div class="row">
            <div class="col-8">
                <h2 class="fw-bold text-primary mb-1">{sop_title_clean}</h2>
                <h5 class="text-muted mb-4">{sop_number}</h5>
            </div>
            <div class="col-4 text-end">
                <div class="badge bg-primary fs-6 mb-2">Version {sop.version}</div>
            </div>
        </div>
        <div class="row border-top pt-3">
            <div class="col-md-6">
                <p class="mb-1"><strong>Effective Date:</strong> {sop.created_at.strftime('%d %b %Y')}</p>
                <p class="mb-1"><strong>Review Date:</strong> {(sop.created_at + timezone.timedelta(days=365)).strftime('%d %b %Y')}</p>
            </div>
            <div class="col-md-6">
                <p class="mb-1"><strong>Author:</strong> {sop.created_by.get_full_name() or sop.created_by.username}</p>
                <p class="mb-1"><strong>Approved By:</strong> Hospital Board / Admin</p>
            </div>
        </div>
    </div>

    <!-- 2. Version Control Table -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">2. Version Control Table</h4>
        {sections['version_control'] or '<p class="text-muted italic">Initial electronic version.</p>'}
    </div>

    <!-- 3. Purpose -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">3. Purpose</h4>
        {sections['purpose'] or '<p>To establish a standard procedure for this operation.</p>'}
    </div>

    <!-- 4. Scope -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">4. Scope</h4>
        {sections['scope'] or '<p>Applies to all relevant departments and staff members at MDH.</p>'}
    </div>

    <!-- 5. Definitions -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">5. Definitions</h4>
        {sections['definitions'] or '<p class="text-muted">No specific definitions provided.</p>'}
    </div>

    <!-- 6. Roles and Responsibilities -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">6. Roles and Responsibilities</h4>
        {sections['roles'] or '<p class="text-muted">Standard roles as per department structure.</p>'}
    </div>

    <!-- 7. Procedure -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">7. Procedure</h4>
        <div class="procedure-steps">
            {sections['procedure'] or '<p class="text-danger">See attached manual content.</p>'}
        </div>
    </div>

    <!-- 8. Related Documents -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">8. Related Documents</h4>
        {sections['related'] or '<p class="text-muted">None specified.</p>'}
    </div>

    <!-- 9. References -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">9. References</h4>
        {sections['references'] or '<p class="text-muted">Hospital Governance Framework.</p>'}
    </div>

    <!-- 10. Revision History -->
    <div class="sop-section mb-4">
        <h4 class="text-secondary fw-bold border-bottom pb-2">10. Revision History</h4>
        {sections['revision'] or '<p class="text-muted">Initial publication in Hub.</p>'}
    </div>
    """
    return html

def run():
    sops = SOP.objects.all()
    print(f"Standardizing {sops.count()} SOPs to MDH Structure...")
    
    for sop in sops:
        sop.content = format_sop(sop)
        sop.save()
        
    print("Standardization Complete!")

if __name__ == '__main__':
    run()
