import os
import shutil
import re
import yaml

SLUGS = ["american-conservatism", "modern-progressive-marxism"]
AI_DATA_DIR = "/win/linux/Code/Text/marginalia/tmp/ai-research-reports/data/md"
HUGO_POSTS_DIR = "/win/linux/Code/Text/marginalia/content/posts"
LEDGER_PATH = "/win/linux/Code/Text/marginalia/data/ai/article_migration.toml"

OMIT_KEYS = [
    "publishDate", "author", "highlight-style", "layout", "build",
    "headless", "type", "toc", "toc-title", "draft", "sitemap",
    "outputs", "toc-depth", "format", "number-sections", "epub-chapter-level",
    "epub-title-page", "epub-stylesheet", "epub_cover_image", "epub-cover-image"
]

def process_article(slug):
    src_dir = os.path.join(AI_DATA_DIR, slug)
    yaml_path = os.path.join(src_dir, "article.yaml")
    md_path = os.path.join(src_dir, "main.md")
    src_media_dir = os.path.join(src_dir, "media", "media")
    
    dest_dir = os.path.join(HUGO_POSTS_DIR, slug)
    dest_media_dir = os.path.join(dest_dir, "media")
    dest_md_path = os.path.join(dest_dir, "index.md")
    
    os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(src_media_dir):
        os.makedirs(dest_media_dir, exist_ok=True)
        for img in os.listdir(src_media_dir):
            shutil.copy2(os.path.join(src_media_dir, img), os.path.join(dest_media_dir, img))
            
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    frontmatter = {}
    frontmatter['title'] = data.get('title', '')
    frontmatter['slug'] = data.get('slug', slug)
    frontmatter['date'] = data.get('date', '')
    if 'description' in data:
        frontmatter['description'] = data['description']
    frontmatter['authors'] = data.get('authors', [])
    frontmatter['categories'] = data.get('categories', [])
    frontmatter['tags'] = data.get('tags', [])
    frontmatter['ai_generated'] = True
    
    meta = {}
    for k, v in data.items():
        if k not in frontmatter and k not in OMIT_KEYS:
            meta[k] = v
    frontmatter['meta'] = meta
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    # Replace image paths in markdown. E.g. data/md/american-conservatism/media/media/rId34.png
    # or just media/media/rId34.png
    md_content = re.sub(r'\]\([^)]*media/media/([^)]+)\)', r'](media/\1)', md_content)
    # Some images might be under assets/media/ or similar. The user mentioned data/md/<slug>/media/media
    md_content = re.sub(r'\]\([^)]*assets/media/([^)]+)\)', r'](media/\1)', md_content)
    md_content = re.sub(r'src="[^"]*media/media/([^"]+)"', r'src="media/\1"', md_content)

    with open(dest_md_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        # Removing the top level title heading because it's usually duplicated by Hugo
        lines = md_content.split('\n')
        if lines and lines[0].startswith('# '):
            lines = lines[1:]
            if lines and lines[0] == '':
                lines = lines[1:]
        f.write('\n'.join(lines))

def update_ledger():
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        ledger_content = f.read()
        
    for slug in SLUGS:
        # Increment total and published documents using regex
        def incr_total(m):
            return f"total_documents = {int(m.group(1)) + 1}"
        def incr_pub(m):
            return f"published_documents = {int(m.group(1)) + 1}"
        ledger_content = re.sub(r'total_documents\s*=\s*(\d+)', incr_total, ledger_content, count=1)
        ledger_content = re.sub(r'published_documents\s*=\s*(\d+)', incr_pub, ledger_content, count=1)
        
        # Append to documents
        entry = f"""
[[documents]]
source_slug = "{slug}"
blog_path = "content/posts/{slug}/index.md"
status = "published"
"""
        ledger_content += entry
        
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        f.write(ledger_content)

if __name__ == "__main__":
    for slug in SLUGS:
        print(f"Processing {slug}...")
        process_article(slug)
    print("Updating ledger...")
    update_ledger()
    print("Migration complete.")
