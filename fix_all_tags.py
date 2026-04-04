import os
import re

def fix_all_template_tags(root_dir):
    # Match {{ ... }} or {% ... %} that contain at least one newline
    # Using dotsall-like logic but matching the brackets
    # This finds {{ followed by anything including newlines until }}
    # and same for {% ... %}
    pattern_var = re.compile(r'\{\{([^}]+)\}\}', re.DOTALL)
    pattern_tag = re.compile(r'\{%([^%]+)%\}\}', re.DOTALL) 
    # Wait, tag is {% ... %}. 
    pattern_tag_correct = re.compile(r'\{%([^%]+)%\}', re.DOTALL)

    for root, dirs, files in os.walk(root_dir):
        if 'venv' in dirs:
            dirs.remove('venv')
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Fix variables: {{ ... }}
                    def join_var(match):
                        inner = match.group(1)
                        if '\n' in inner:
                            # Join lines, collapse whitespace
                            joined = " ".join(line.strip() for line in inner.split('\n'))
                            return f"{{{{ {joined.strip()} }}}}"
                        return match.group(0)
                    
                    content = pattern_var.sub(join_var, content)
                    
                    # Fix tags: {% ... %}
                    def join_tag(match):
                        inner = match.group(1)
                        if '\n' in inner:
                            # Join lines, collapse whitespace
                            joined = " ".join(line.strip() for line in inner.split('\n'))
                            return f"{{% {joined.strip()} %}}"
                        return match.group(0)
                    
                    content = pattern_tag_correct.sub(join_tag, content)
                    
                    if content != original_content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"FIXED TAGS IN: {path}")
                        
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    fix_all_template_tags('mdh_intranet')
