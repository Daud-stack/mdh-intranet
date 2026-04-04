
from docx import Document
from docx.document import Document as DocType
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

doc = Document(r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx")
table_target = 5
count = 0
for i, child in enumerate(doc.element.body.iterchildren()):
    if isinstance(child, CT_Tbl):
        if count == table_target:
            print(f"Table {table_target} is at Block Index {i}")
            # print surrounding 5 blocks
            print("Surrounding blocks:")
            for j, c in enumerate(doc.element.body.iterchildren()):
                if j >= i - 5 and j <= i + 5:
                    print(f"[{j}] {'Table' if isinstance(c, CT_Tbl) else 'Para'}")
            break
        count += 1
