import os
import re

def scan_templates(root_dir):
    pattern = re.compile(r'\{\{\s*\n')
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in dirs:
            dirs.remove('venv')
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.search(content):
                            print(f"FOUND SPLIT TAG IN: {path}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    scan_templates('mdh_intranet')
