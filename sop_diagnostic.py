
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
    report = []

    sections = [
        "1. HEADER_TABLE", "2. CONTROL BOX", "3. DISTRIBUTION LIST", 
        "4. CHANGE HISTORY", "5. PURPOSE", "6. SCOPE", "7. DEFINITIONS", 
        "8. ROLES & RESPONSIBILITIES", "9. REQUIRED MATERIALS", "10. PROCEDURE", 
        "11. HIGH-ALERT", "12. SAFETY", "13. DOCUMENTATION", "14. REFERENCES"
    ]

    print(f"Starting Diagnostic on {total} SOPs...\n")

    for sop in sops:
        soup = BeautifulSoup(sop.content, 'html.parser')
        text = sop.content
        
        missing = []
        # Check for first table
        has_header_table = soup.find('table') is not None
        if not has_header_table:
            missing.append("1. HEADER_TABLE")

        # Check for numeric headers
        for i in range(2, 15):
            pattern = f"{i}\."
            if pattern not in text:
                # Find the section name to report
                sec_name = [s for s in sections if s.startswith(f"{i}.")][0]
                missing.append(sec_name)

        # Check for "N/A" indicating empty sections
        nas = text.count(">N/A<") + text.count(" N/A ")
        
        report.append({
            'code': sop.title.split('-')[0].strip() if '-' in sop.title else '??',
            'title': sop.title,
            'missing_count': len(missing),
            'missing': missing,
            'na_count': nas,
            'score': (14 - len(missing)) / 14 * 100
        })

    # Sort by score ascending (worst first)
    report.sort(key=lambda x: x['score'])

    print(f"{'CODE':<15} | {'SCORE':<5} | {'MISSING SECTIONS'}")
    print("-" * 70)
    for r in report[:10]:
        missing_str = ", ".join(r['missing'][:3]) + ("..." if len(r['missing']) > 3 else "")
        print(f"{r['code']:<15} | {r['score']:>4.1f}% | {missing_str}")

    avg_score = sum(r['score'] for r in report) / total
    print("-" * 70)
    print(f"AVERAGE HEALTH SCORE: {avg_score:.2f}%")
    
    # Analyze common failures
    failure_counts = {}
    for r in report:
        for m in r['missing']:
            failure_counts[m] = failure_counts.get(m, 0) + 1
            
    print("\nMOST FREQUENTLY MISSING SECTIONS:")
    sorted_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
    for sec, count in sorted_failures[:5]:
        print(f"- {sec}: {count} SOPs")

if __name__ == "__main__":
    run_diagnostic()
