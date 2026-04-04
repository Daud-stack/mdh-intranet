import os

def check_files(dir_path):
    print("Checking directory: " + dir_path)
    for root, dirs, files in os.walk(dir_path):
        if 'venv' in root or '.git' in root: continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if '{%' in line and '%}' not in line:
                            print("SPLIT {% in " + path + " at line " + str(i+1))
                        if '{{' in line and '}}' not in line:
                            print("SPLIT {{ in " + path + " at line " + str(i+1))

check_files(r'c:\Users\HomePC\mdh_intranet\mdh_intranet')
