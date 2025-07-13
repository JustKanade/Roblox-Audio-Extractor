import os

EXCLUDED_DIRS = {'.git', '.github', 'node_modules', '__pycache__', 'venv', 'env', 'docs'}
MAX_DEPTH = 5
OUTPUT_FILE = 'docs/STRUCTURE.md'

def generate_structure(path='.', depth=0, max_depth=MAX_DEPTH):
    if depth > max_depth:
        return ''
    output = ''
    try:
        entries = sorted(os.listdir(path))
    except Exception:
        return ''
    for entry in entries:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, '.')
        if os.path.isdir(full_path):
            if entry in EXCLUDED_DIRS:
                continue
            output += '  ' * depth + f'-  **{entry}**\n'
            output += generate_structure(full_path, depth + 1, max_depth)
        else:
            markdown_link = f'[{entry}]({rel_path.replace(" ", "%20")})'
            output += '  ' * depth + f'-  {markdown_link}\n'
    return output

if __name__ == '__main__':
    os.makedirs('docs', exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('# 📚 Project Structure\n\n')
        f.write(generate_structure())
