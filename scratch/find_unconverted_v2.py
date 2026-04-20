import os
import re
from pathlib import Path

REPO_ROOT = Path("/win/linux/Code/Text/marginalia")
DOCX_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "docx"
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"
POSTS_ROOT = REPO_ROOT / "content" / "posts"

def norm_title(s: str) -> str:
    s = s.lower()
    s = (
        s.replace("—", "-")
        .replace("–", "-")
        .replace("‑", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
    )
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def get_items(root):
    items = []
    if not root.exists():
        return items
    for p in root.iterdir():
        if p.is_dir():
            items.append(norm_title(p.name))
        elif p.suffix == ".md":
            items.append(norm_title(p.stem))
    return items

def main():
    docx_files = list(DOCX_ROOT.rglob("*.docx"))
    md_norms = get_items(MD_ROOT)
    post_norms = get_items(POSTS_ROOT)
    
    unconverted = []
    for docx in docx_files:
        d_norm = norm_title(docx.stem)
        matched = False
        for m_norm in md_norms + post_norms:
            if m_norm and d_norm and (m_norm in d_norm or d_norm in m_norm):
                matched = True
                break
        if not matched:
            unconverted.append(docx)
            
    print(f"Unconverted ({len(unconverted)}):")
    for u in sorted(unconverted):
        print(f"  - {u.relative_to(DOCX_ROOT)}")

if __name__ == "__main__":
    main()
