
import os
import re

path = r'c:\Users\HomePC\mdh_intranet\mdh_intranet\capa\templates\capa\capa_detail.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Generic regex to find {{ ... }} blocks that are split across lines and merge them
def merge_split_tags(text):
    # Merge {{ ... }}
    text = re.sub(r'\{\{\s*\n\s*([^}]+)\s*\}\}', r'{{ \1 }}', text)
    # Merge {% ... %}
    text = re.sub(r'\{%\s*if\s+([^%]+)\s*\n\s*([^%]+)\s*%\}', r'{% if \1 \2 %}', text)
    return text

content = merge_split_tags(content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Cleanup with regex complete.")
