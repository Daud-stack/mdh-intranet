import os
import re

def find_split_tags(directory):
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Find {% ... %} spanning multiple lines
                        matches = re.finditer(r'\{%[^%]*?\n.*?%\}', content, re.DOTALL)
                        for match in matches:
                            print(f"SPLIT TAG in {path}:")
                            print(match.group())
                            print("-" * 20)
                            
                        # Find {{ ... }} spanning multiple lines
                        matches = re.finditer(r'\{\{[^}]*?\n.*?\}\}', content, re.DOTALL)
                        for match in matches:
                            print(f"SPLIT {{}} in {path}:")
                            print(match.group())
                            print("-" * 20)
                except Exception as e:
                    print(f"Error reading {path}: {e}")

if __name__ == '__main__':
    base_dir = r'c:\Users\HomePC\mdh_intranet'
    find_split_tags(base_dir)
