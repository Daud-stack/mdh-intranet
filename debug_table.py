
from docx import Document
import re

doc = Document(r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx")
t = doc.tables[5]
print(f"Table 5 Rows: {len(t.rows)}")
for i, r in enumerate(t.rows):
    cells = [c.text.strip() for c in r.cells]
    print(f"Row {i}: {cells}")

def split_role_responsibility(text):
    words = text.split()
    SOP_VERBS = {'Collect', 'Issue', 'Perform', 'Approve', 'Oversee', 'Ensure', 'Manage', 'Handle', 'Record'} # shortened for debug
    limit = min(5, len(words))
    for i in range(1, limit):
        word = words[i].strip(',. ')
        if word in SOP_VERBS:
            return " ".join(words[:i]), " ".join(words[i:])
    return text, ""

print("\nTesting split logic on Row 2 Cell 0:")
text = t.rows[2].cells[0].text.strip()
clean_text = re.sub(r'^[\-\s•]+', '', text)
role, resp = split_role_responsibility(clean_text)
print(f"Original: {repr(text)}")
print(f"Cleaned: {repr(clean_text)}")
print(f"Split: ROLE='{role}' | RESP='{resp}'")
