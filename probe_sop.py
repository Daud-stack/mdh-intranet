
import os
import django
from docx import Document as DocxDocument
import re
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.documents.models import Document

def probe_sop(doc_id, start_code):
    d = Document.objects.get(id=doc_id)
    doc = DocxDocument(d.file.path)
    found = False
    count = 0
    
    for element in doc.element.body.iterchildren():
        if isinstance(element, CT_P):
            p = Paragraph(element, doc)
            text = p.text.strip()
            if start_code in text:
                found = True
            if found:
                print(f"P: {text}")
                count += 1
        elif isinstance(element, CT_Tbl):
            if found:
                t = Table(element, doc)
                data = [[c.text.strip() for c in r.cells] for r in t.rows]
                print(f"T: {data}")
                count += 1
        
        if count > 50:
            break

if __name__ == "__main__":
    probe_sop(4, "MDH-CLIN-001")
