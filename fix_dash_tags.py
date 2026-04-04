import os
import re

path = r'C:\Users\HomePC\mdh_intranet\mdh_intranet\dashboard\templates\dashboard\index.html'

if not os.path.exists(path):
    print(f"Error: {path} not found")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to join split tags like {{ \n variable }}
# Group 1 captures the variable content
content = re.sub(r'\{\{\s*\n\s*([^}]+)\s*\}\}', r'{{ \1 }}', content)

# Specific fix for req.get_status_display
content = re.sub(r'\{\{\s*\n\s*req\.get_status_display\s*\}\}', r'{{ req.get_status_display }}', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"FIXED {path} tags")
