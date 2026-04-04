"""Verify: scan for any remaining split template tags."""
import os, re

ROOT = os.path.join(os.path.dirname(__file__), 'mdh_intranet')
SPLIT_VAR = re.compile(r'\{\{([^}]*?\n[^}]*?)\}\}', re.DOTALL)
SPLIT_BLK = re.compile(r'\{%([^%]*?\n[^%]*?)%\}', re.DOTALL)

remaining = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ('venv', '__pycache__', 'migrations', '.git')]
    for fname in filenames:
        if not fname.endswith('.html'):
            continue
        filepath = os.path.join(dirpath, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        for m in SPLIT_VAR.finditer(content):
            rel = os.path.relpath(filepath, ROOT)
            line = content[:m.start()].count('\n') + 1
            print(f"  SPLIT {{ tag at {rel}:{line}: {m.group(0).strip()[:100]}")
            remaining += 1
        for m in SPLIT_BLK.finditer(content):
            rel = os.path.relpath(filepath, ROOT)
            line = content[:m.start()].count('\n') + 1
            print(f"  SPLIT {{% tag at {rel}:{line}: {m.group(0).strip()[:100]}")
            remaining += 1

if remaining == 0:
    print("ALL CLEAR - No split template tags found anywhere.")
else:
    print(f"\nWARNING: {remaining} split tags still remain!")
