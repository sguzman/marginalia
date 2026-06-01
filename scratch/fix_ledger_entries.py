import re

LEDGER_PATH = "/win/linux/Code/Text/marginalia/data/ai/article_migration.toml"

with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the bad entries start
bad_entries_start = content.find('\n[[documents]]\nsource_slug = "american-conservatism"')

if bad_entries_start != -1:
    content = content[:bad_entries_start]
    
    correct_entries = """
[[documents]]
source_slug = "american-conservatism"
title = "American Conservatism and the Liberal-Revolutionary Founding"
source_date = "2026-06-01"
docx_file = "American Conservatism and the Liberal-Revolutionary Founding.docx"
source_kind = "docx"
md_path = "tmp/ai-research-reports/data/md/american-conservatism/main.md"
meta_path = "tmp/ai-research-reports/data/md/american-conservatism/article.yaml"
crosswalk_match_basis = "manual"
added = true
blog_slug = "american-conservatism"
blog_path = "content/posts/american-conservatism/index.md"
note = ""
status = "published"

[[documents]]
source_slug = "modern-progressive-marxism"
title = "Formalizing the Connection Between Modern Progressive Politics and Marxism"
source_date = "2026-06-01"
docx_file = "Formalizing the Connection Between Modern Progressive Politics and Marxism.docx"
source_kind = "docx"
md_path = "tmp/ai-research-reports/data/md/modern-progressive-marxism/main.md"
meta_path = "tmp/ai-research-reports/data/md/modern-progressive-marxism/article.yaml"
crosswalk_match_basis = "manual"
added = true
blog_slug = "modern-progressive-marxism"
blog_path = "content/posts/modern-progressive-marxism/index.md"
note = ""
status = "published"
"""
    content += correct_entries
    
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed ledger.")
else:
    print("Could not find the bad entries.")
