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
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if '{%' in line and '%}' not in line:
                                print(f"POSSIBLE SPLIT tag in {path} line {i+1}:")
                                print(line.strip())
                            if '{{' in line and '}}' not in line:
                                print(f"POSSIBLE SPLIT var in {path} line {i+1}:")
                                print(line.strip())
                except Exception as e:
                    pass

find_split_tags(r'c:\Users\HomePC\mdh_intranet')
