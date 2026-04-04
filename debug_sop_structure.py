
from docx import Document
import re

file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"

doc = Document(file_path)

# Find first occurrence of MDH-FIN-001 and show context
all_text = '\n'.join([p.text for p in doc.paragraphs])
lines = all_text.split('\n')

for i, line in enumerate(lines[:500]):
    if 'MDH-FIN-001' in line:
        print(f"Found at line {i}:")
        print("="*80)
        # Show 20 lines of context
        for j in range(max(0, i-5), min(len(lines), i+20)):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j}: {lines[j][:120]}")
        print("="*80)
        break
