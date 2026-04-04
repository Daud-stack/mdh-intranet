"""Fix split template tags in dashboard templates."""
import os
import re

base = r"c:\Users\HomePC\mdh_intranet\mdh_intranet\dashboard\templates\dashboard"
files_to_fix = ["index.html", "schedule.html", "settings.html"]

for fname in files_to_fix:
    fpath = os.path.join(base, fname)
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
        
    with open(fpath, "rb") as f:
        content = f.read().decode("utf-8")
    
    original = content
    
    # Pass 1: Join split {{ }} tags
    # Handle both Unix and Windows line endings
    content = re.sub(r'\{\{\s*\r?\n\s*', '{{ ', content)
    content = re.sub(r'\s*\r?\n\s*\}\}', ' }}', content)
    
    # Pass 2: Join split {% %} tags 
    content = re.sub(r'\{%\s*\r?\n\s*', '{% ', content)
    content = re.sub(r'\s*\r?\n\s*%\}', ' %}', content)
    
    if content != original:
        with open(fpath, "wb") as f:
            f.write(content.encode("utf-8"))
        print(f"FIXED: {fname}")
    else:
        print(f"  OK:  {fname}")

print("\nDone!")
