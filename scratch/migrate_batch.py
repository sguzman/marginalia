import os
import shutil
import yaml
import re
from datetime import datetime

SLUGS = [
    "intergenerational-extraction-in-liberal-democracies",
    "liberalism-as-political-domestication",
    "liberalism-equality-and-the-leftward-drift-thesis",
    "liberalism-social-disembedding-and-managed-dependency",
    "republicans-as-moderating-opposition-without-a-rival-order",
    "the-female-shadow"
]

LEDGER_PATH = "/win/linux/Code/Text/marginalia/data/ai/article_migration.toml"

OMIT_KEYS = [
    "build", "cascade", "sitemap", "resources", "headless", "isCJKLanguage",
    "translationKey", "epub-stylesheet", "highlight-style", "author",
    "publishDate", "series", "series-title", "series-number", "series_title",
    "series_number", "report-no", "report-number", "report-year", "report_no",
    "report_number", "report_year", "report_series", "report_series_title",
    "report_series_number", "format", "number-sections", "epub-chapter-level",
    "epub-title-page", "epub_cover_image", "epub-cover-image", "layout", "type",
    "toc", "toc-title", "toc-depth", "outputs", "draft"
]

def migrate_slug(slug):
    AI_MD_DIR = f"/win/linux/Code/Text/marginalia/tmp/ai-research-reports/data/md/{slug}"
    BLOG_POSTS_DIR = f"/win/linux/Code/Text/marginalia/content/posts/{slug}"
    
    yaml_path = os.path.join(AI_MD_DIR, "article.yaml")
    md_path = os.path.join(AI_MD_DIR, "main.md")
    
    if not os.path.exists(yaml_path) or not os.path.exists(md_path):
        print(f"Skipping {slug}, files not found.")
        return

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Fix image paths (media/media/... to media/...)
    markdown_content = re.sub(r'\]\([^)]*media/media/([^)]+)\)', r'](media/\1)', markdown_content)
    
    # Fix image indentation and multi-line wrapping
    def repl_img(m):
        alt = re.sub(r'\s+', ' ', m.group(1)).strip()
        url = re.sub(r'\s+', '', m.group(2))
        return f"![{alt}]({url})"
    
    markdown_content = re.sub(r'^[ \t]*!\[([^\]]*)\]\(([^)]*)\)(?:\{[^}]*\})?', repl_img, markdown_content, flags=re.MULTILINE)

    # Clean up dashes around images if any
    markdown_content = re.sub(r'  [-]+\n(!\[.*?\]\(.*?\))\n\n  [-]+', r'\1\n', markdown_content)
    markdown_content = re.sub(r'  [-]+\n(!\[.*?\]\(.*?\))\n  [-]+', r'\1\n', markdown_content)
    markdown_content = re.sub(r'  [-]+\n(!\[.*?\]\(.*?\))\n', r'\1\n', markdown_content)

    # Construct frontmatter
    frontmatter = {}
    frontmatter['title'] = data.get('title', slug.replace("-", " ").title())
    frontmatter['linkTitle'] = data.get('linkTitle', frontmatter['title'])
    frontmatter['description'] = data.get('description', '')
    frontmatter['summary'] = data.get('abstract', data.get('summary', ''))
    frontmatter['slug'] = data.get('slug', slug)
    frontmatter['date'] = data.get('date', datetime.today().strftime('%Y-%m-%d'))
    frontmatter['lastmod'] = data.get('lastmod', frontmatter['date'])
    frontmatter['draft'] = False
    frontmatter['authors'] = data.get('authors', [])
    frontmatter['categories'] = data.get('categories', [])
    frontmatter['tags'] = data.get('tags', [])
    frontmatter['keywords'] = data.get('keywords', [])
    frontmatter['layout'] = "single"
    frontmatter['markup'] = "goldmark"
    frontmatter['outputs'] = ["HTML", "RSS"]
    frontmatter['ai_generated'] = True
    
    meta = {}
    for k, v in data.items():
        if k not in OMIT_KEYS:
            meta[k] = v
    frontmatter['meta'] = meta

    # Create directory and copy media
    os.makedirs(BLOG_POSTS_DIR, exist_ok=True)
    src_media = os.path.join(AI_MD_DIR, "media")
    dest_media = os.path.join(BLOG_POSTS_DIR, "media")
    if os.path.exists(src_media):
        if os.path.exists(dest_media):
            shutil.rmtree(dest_media)
        src_media_inner = os.path.join(src_media, "media")
        if os.path.exists(src_media_inner):
            shutil.copytree(src_media_inner, dest_media)
        else:
            shutil.copytree(src_media, dest_media)

    # Write index.md
    dest_md_path = os.path.join(BLOG_POSTS_DIR, "index.md")
    with open(dest_md_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        f.write(markdown_content)

    print(f"Migrated {slug}")

    # Update ledger
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        ledger = f.read()
    
    if slug not in ledger:
        total_match = re.search(r'^total_documents\s*=\s*(\d+)', ledger, re.MULTILINE)
        pub_match = re.search(r'^published_documents\s*=\s*(\d+)', ledger, re.MULTILINE)
        if total_match and pub_match:
            total = int(total_match.group(1)) + 1
            pub = int(pub_match.group(1)) + 1
            ledger = re.sub(r'^total_documents\s*=\s*\d+', f'total_documents = {total}', ledger, count=1, flags=re.MULTILINE)
            ledger = re.sub(r'^published_documents\s*=\s*\d+', f'published_documents = {pub}', ledger, count=1, flags=re.MULTILINE)
        
        # We can extract the original docx_file by cross-referencing if needed, or just set it manually based on title
        docx_file = data.get('docx_source', f"{frontmatter['title']}.docx")

        new_block = f"""
[[documents]]
source_slug = "{slug}"
title = "{frontmatter['title']}"
source_date = "{frontmatter['date']}"
docx_file = "{docx_file}"
source_kind = "docx"
md_path = "tmp/ai-research-reports/data/md/{slug}/main.md"
meta_path = "tmp/ai-research-reports/data/md/{slug}/article.yaml"
crosswalk_match_basis = "manual"
added = true
blog_slug = "{slug}"
blog_path = "content/posts/{slug}/index.md"
note = ""
status = "published"
"""
        ledger += new_block
        with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
            f.write(ledger)
        print(f"Updated ledger for {slug}")
    else:
        print(f"Article {slug} already in ledger.")

for s in SLUGS:
    migrate_slug(s)
