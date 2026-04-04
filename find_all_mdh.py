
from docx import Document
import re

file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"

doc = Document(file_path)

# Let's look at the bigger picture - find ALL lines with MDH codes
mdh_lines = []
for i, para in enumerate(doc.paragraphs):
    if re.search(r'MDH-[A-Z]{2,4}-\d{3}', para.text):
        mdh_lines.append((i, para.text.strip()[:150]))

print(f"Total lines with MDH codes: {len(mdh_lines)}\n")
print("First 30:")
for idx, text in mdh_lines[:30]:
    print(f"Para {idx}: {text}")
