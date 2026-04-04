
import os
import django
from docx import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.documents.models import Document

def extract_tables_for_sop(doc_id, start_code, end_code):
    d = Document.objects.get(id=doc_id)
    doc = DocxDocument(d.file.path)
    found = False
    
    for element in doc.element.body.iterchildren():
        if isinstance(element, CT_P):
            p = Paragraph(element, doc)
            text = p.text.strip()
            if start_code in text:
                found = True
            elif found and end_code in text:
                break
        elif isinstance(element, CT_Tbl) and found:
            t = Table(element, doc)
            data = [[c.text.strip() for c in r.cells] for r in t.rows]
            print(f"TABLE_START")
            for row in data:
                print(row)
            print(f"TABLE_END")

if __name__ == "__main__":
    extract_tables_for_sop(4, "MDH-FIN-001", "MDH-FIN-002")
