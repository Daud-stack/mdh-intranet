
from docx import Document
import os
import re

file_path = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\MDH_SOP_Manual_Full_Content.docx"

doc = Document(file_path)

# Let's count all MDH codes in the document
codes_found = []

for para in doc.paragraphs:
    text = para.text.strip()
    # Find all MDH codes
    matches = re.findall(r'(MDH-[A-Z]{2,4}-\d{3})', text)
    for match in matches:
        codes_found.append((match, text[:100]))

print(f"Found {len(codes_found)} MDH code occurrences\n")
print("First 50 unique codes:")
unique_codes = list(dict.fromkeys([c[0] for c in codes_found]))
for i, code in enumerate(unique_codes[:50]):
    print(f"{i+1}. {code}")

print(f"\n\nTotal unique codes: {len(unique_codes)}")
