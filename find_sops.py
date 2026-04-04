
import os
import django
from docx import Document as DocxDocument
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.documents.models import Document

def find_sops(doc_id):
    d = Document.objects.get(id=doc_id)
    doc = DocxDocument(d.file.path)
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if re.search(r'MDH-[A-Z]+-\d+', t) and len(t) < 100:
            print(f"[{i}] {t}")
        if i > 1000:
            break

if __name__ == "__main__":
    find_sops(4)
