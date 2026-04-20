import os
import re
from pathlib import Path

REPO_ROOT = Path("/win/linux/Code/Text/marginalia")
DOCX_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "docx"
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"

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

def get_md_items():
    items = []
    if not MD_ROOT.exists():
        return items
    for d in MD_ROOT.iterdir():
        if d.is_dir():
            if (d / "main.md").exists() and (d / "article.yaml").exists():
                items.append(norm_title(d.name))
    return items

def main():
    docx_files = list(DOCX_ROOT.rglob("*.docx"))
    md_norms = get_md_items()
    
    unconverted = []
    for docx in docx_files:
        d_norm = norm_title(docx.stem)
        matched = False
        for m_norm in md_norms:
            # The sync script uses: if it.norm and dn and (it.norm in dn or dn in it.norm):
            if m_norm and d_norm and (m_norm in d_norm or d_norm in m_norm):
                matched = True
                break
        if not matched:
            unconverted.append(docx)
            
    print(f"Found {len(docx_files)} DOCX files.")
    print(f"Found {len(md_norms)} converted MD projects.")
    print(f"Unconverted ({len(unconverted)}):")
    for u in sorted(unconverted):
        print(f"  - {u.relative_to(DOCX_ROOT)}")

if __name__ == "__main__":
    main()
