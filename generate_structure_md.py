import os

EXCLUDED_DIRS = {'.git', '.github', 'node_modules', '__pycache__', 'venv', 'env', 'docs'}
MAX_DEPTH = 5
OUTPUT_FILE = 'docs/STRUCTURE.md'

def generate_tree(path='.', prefix='', depth=0):
    if depth > MAX_DEPTH:
        return ''
    output = ''
    try:
        entries = sorted(os.listdir(path))
    except Exception:
        return ''
    entries = [e for e in entries if e not in EXCLUDED_DIRS and not e.startswith('.')]
    for i, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, '.')
        connector = '└── ' if i == len(entries) - 1 else '├── '
        if os.path.isdir(full_path):
            output += f'{prefix}{connector}{entry}/\n'
            extension = '    ' if i == len(entries) - 1 else '│   '
            output += generate_tree(full_path, prefix + extension, depth + 1)
        else:
            markdown_link = f'[{entry}]({rel_path.replace(" ", "%20")})'
            output += f'{prefix}{connector}{markdown_link}\n'
    return output

if __name__ == '__main__':
    os.makedirs('docs', exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('# Project Structure\n\n')
        f.write('```\n')
        f.write(generate_tree())
        f.write('```\n')
