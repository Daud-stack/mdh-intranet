
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P): yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl): yield Table(child, parent)

doc = Document(r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx")
print("Probing SOP 1 start area...")
for i, block in enumerate(iter_block_items(doc)):
    if i < 400: continue
    if i > 700: break
    
    if isinstance(block, Table):
        text = "|".join(c.text.strip() for r in block.rows for c in r.cells)[:150]
        print(f"[{i}] TABLE: {text}")
    else:
        text = block.text.strip()
        if text: print(f"[{i}] PARA: {text[:150]}")
