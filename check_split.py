import os

def check_files(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find all {% matches
                    pos = 0
                    while True:
                        start = content.find('{%', pos)
                        if start == -1: break
                        end = content.find('%}', start)
                        if end == -1:
                            print(f"BROKEN {% in {path} at pos {start}")
                            break
                        tag = content[start:end+2]
                        if '\n' in tag:
                            print(f"SPLIT TAG in {path}:")
                            print(repr(tag))
                        pos = end + 2
                    
                    pos = 0
                    while True:
                        start = content.find('{{', pos)
                        if start == -1: break
                        end = content.find('}}', start)
                        if end == -1:
                            print(f"BROKEN {{ in {path} at pos {start}")
                            break
                        tag = content[start:end+2]
                        if '\n' in tag:
                            print(f"SPLIT VAR in {path}:")
                            print(repr(tag))
                        pos = end + 2

check_files(r'c:\Users\HomePC\mdh_intranet\mdh_intranet\dashboard\templates\dashboard')
