import os
import re

def find_split_tags(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
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

find_split_tags(r'c:\Users\HomePC\mdh_intranet\mdh_intranet\templates')
find_split_tags(r'c:\Users\HomePC\mdh_intranet\mdh_intranet\dashboard\templates\dashboard')
