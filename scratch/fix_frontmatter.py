import os
import yaml

SLUGS = ["american-conservatism", "modern-progressive-marxism"]
AI_DATA_DIR = "/win/linux/Code/Text/marginalia/tmp/ai-research-reports/data/md"
HUGO_POSTS_DIR = "/win/linux/Code/Text/marginalia/content/posts"

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

def process_article(slug):
    src_dir = os.path.join(AI_DATA_DIR, slug)
    yaml_path = os.path.join(src_dir, "article.yaml")
    
    dest_dir = os.path.join(HUGO_POSTS_DIR, slug)
    dest_md_path = os.path.join(dest_dir, "index.md")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    frontmatter = {}
    frontmatter['title'] = data.get('title', '')
    frontmatter['linkTitle'] = data.get('linkTitle', data.get('title', ''))
    frontmatter['description'] = data.get('description', '')
    
    # "Set summary from meta.abstract when the abstract is strong, otherwise from the first clean paragraph."
    frontmatter['summary'] = data.get('abstract', data.get('summary', ''))
    
    frontmatter['slug'] = data.get('slug', slug)
    frontmatter['date'] = data.get('date', '')
    frontmatter['lastmod'] = data.get('lastmod', data.get('date', ''))
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
            
    # "When the same concept exists at top level and under meta, keep the top-level field as the Hugo-facing value and keep the richer/canonical detail under meta."
    # Wait, the rule says "mirror taxonomies across top level and meta when meta.categories... are present"
    # The actual data from article.yaml is all we have. We just filtered it by OMIT_KEYS.
    frontmatter['meta'] = meta
    
    # Read the existing index.md to extract just the markdown content, discarding the old frontmatter.
    with open(dest_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # strip existing frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            markdown_content = parts[2].lstrip()
        else:
            markdown_content = content
    else:
        markdown_content = content
        
    with open(dest_md_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        f.write("---\n")
        f.write(markdown_content)

if __name__ == "__main__":
    for slug in SLUGS:
        process_article(slug)
    print("Fixed frontmatter.")
