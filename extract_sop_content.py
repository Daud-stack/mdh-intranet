
import os
import django
from docx import Document as DocxDocument
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.documents.models import Document

def extract_sop(doc_id, sop_code):
    d = Document.objects.get(id=doc_id)
    doc = DocxDocument(d.file.path)
    content = []
    found = False
    
    # Iterate through all elements (paragraphs and tables) in order
    for element in doc.element.body.iterchildren():
        from docx.oxml.text.paragraph import CT_P
        from docx.oxml.table import CT_Tbl
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        
        if isinstance(element, CT_P):
            p = Paragraph(element, doc)
            text = p.text.strip()
            if sop_code in text:
                found = True
            elif found and re.search(r'MDH-[A-Z]+-\d+', text) and text != sop_code:
                # Found next SOP, stop
                break
            
            if found and text:
                content.append(text)
                
        elif isinstance(element, CT_Tbl):
            t = Table(element, doc)
            table_data = []
            for row in t.rows:
                table_data.append([cell.text.strip() for cell in row.cells])
            
            # Check if this table belongs to the SOP
            table_text = " ".join([" ".join(row) for row in table_data])
            if sop_code in table_text:
                found = True
            
            if found:
                content.append(table_data)
                
    return content

if __name__ == "__main__":
    sop_data = extract_sop(4, "MDH-CLIN-001")
    for item in sop_data:
        print(item)
