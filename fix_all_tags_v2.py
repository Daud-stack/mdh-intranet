import os
import re

def fix_split_tags(directory):
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix {% ... %}
                    new_content = re.sub(r'\{%([^%]*?)\n(.*?)\%\}', lambda m: '{%' + m.group(1).strip() + ' ' + m.group(2).strip() + ' %}', content, flags=re.DOTALL)
                    
                    # Fix {{ ... }}
                    new_content = re.sub(r'\{\{([^}]*?)\n(.*?)\}\}', lambda m: '{{ ' + m.group(1).strip() + ' ' + m.group(2).strip() + ' }}', new_content, flags=re.DOTALL)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed tags in {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == '__main__':
    base_dir = r'c:\Users\HomePC\mdh_intranet'
    fix_split_tags(base_dir)
