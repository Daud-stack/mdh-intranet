
import os
import django
import re
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()
from mdh_intranet.sop_manual.models import SOP

def run_diagnostic():
    sops = SOP.objects.all()
    total = sops.count()
    if total == 0:
        print("No SOPs found in database.")
        return

    print(f"Starting Diagnostic on {total} SOPs...\n")

    failure_counts = {i: 0 for i in range(1, 15)}
    samples = []

    for sop in sops:
        content = sop.content
        missing = []
        
        # Check specifically for the headers we tried to inject
        # Points 2 to 14 were injected as "### {num}. {display}" -> "<h3>{num}. {display}</h3>"
        for i in range(2, 15):
            if f">{i}." not in content and f" {i}." not in content:
                failure_counts[i] += 1
                missing.append(i)
        
        # Check for first table (Header)
        if "<table" not in content:
            failure_counts[1] += 1
            missing.append(1)

        if len(missing) > 5:
            samples.append((sop.title, missing))

    print(f"{'SECTION':<30} | {'MISSING COUNT':<15} | {'HEALTH %'}")
    print("-" * 65)
    
    sections = [
        "1. HEADER_TABLE", "2. CONTROL BOX", "3. DISTRIBUTION LIST", 
        "4. CHANGE HISTORY", "5. PURPOSE", "6. SCOPE", "7. DEFINITIONS", 
        "8. ROLES & RESPONSIBILITIES", "9. REQUIRED MATERIALS", "10. PROCEDURE", 
        "11. HIGH-ALERT", "12. SAFETY", "13. DOCUMENTATION", "14. REFERENCES"
    ]

    for i, name in enumerate(sections, 1):
        count = failure_counts[i]
        health = ((total - count) / total) * 100
        print(f"{name:<30} | {count:<15} | {health:>7.1f}%")

    print("\nPROBING ERROR IN SOP CONTENT:")
    if sops.exists():
        first = sops.first()
        print(f"SOP: {first.title}")
        print("Heads found:")
        for i in range(1, 15):
            found = f"{i}." in first.content
            print(f"  {i}.: {'YES' if found else 'NO'}")
        
if __name__ == "__main__":
    run_diagnostic()
