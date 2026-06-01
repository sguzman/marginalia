import os
import re

FILES = [
    "/win/linux/Code/Text/marginalia/content/posts/american-conservatism/index.md",
    "/win/linux/Code/Text/marginalia/content/posts/modern-progressive-marxism/index.md"
]

def fix_images(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    def repl(m):
        # Collapse whitespace/newlines in alt text
        alt = re.sub(r'\s+', ' ', m.group(1)).strip()
        # Remove any whitespace/newlines in URL
        url = re.sub(r'\s+', '', m.group(2))
        
        # Build clean image markdown, without the trailing {} dimensions
        return f"![{alt}]({url})"

    # Regex looks for ![alt](url) optionally followed by {dimensions}
    # It handles newlines inside the alt brackets and the dimension braces.
    new_content = re.sub(r'!\[([^\]]*)\]\(([^)]*)\)(?:\{[^}]*\})?', repl, content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed images in {file_path}")

for p in FILES:
    if os.path.exists(p):
        fix_images(p)
    else:
        print(f"Not found: {p}")
