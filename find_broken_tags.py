import os
import re

def find_broken_tags(directory):
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Count opening and closing
                        open_tags = content.count('{%')
                        close_tags = content.count('%}')
                        if open_tags != close_tags:
                            print(f"UNBALANCED {{% in {path}: {open_tags} vs {close_tags}")
                            
                        open_vars = content.count('{{')
                        close_vars = content.count('}}')
                        if open_vars != close_vars:
                            print(f"UNBALANCED {{{{ in {path}: {open_vars} vs {close_vars}")
                            
                except Exception as e:
                    pass

find_broken_tags(r'c:\Users\HomePC\mdh_intranet')
