import os
import re
import yaml
from pathlib import Path
from dataclasses import dataclass

REPO_ROOT = Path("/win/linux/Code/Text/marginalia")
DOCX_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "docx"
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"

def norm_title(s: str) -> str:
    if not s: return ""
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

def load_yaml_first_doc(path: Path):
    try:
        docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        for doc in docs:
            if isinstance(doc, dict) and doc:
                return doc
    except:
        pass
    return {}

def read_h1(path: Path):
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:12]:
            if line.startswith("# "):
                return line[2:].strip()
    except:
        pass
    return None

@dataclass
class MdItem:
    folder_name: str
    title: str
    norm: str

def collect_md_items():
    items = []
    for d in sorted([p for p in MD_ROOT.iterdir() if p.is_dir()]):
        meta_path = d / "article.yaml"
        md_path = d / "main.md"
        title = None
        if meta_path.exists():
            meta = load_yaml_first_doc(meta_path)
            title = meta.get("title")
        if not title and md_path.exists():
            title = read_h1(md_path)
        if title:
            items.append(MdItem(folder_name=d.name, title=str(title), norm=norm_title(str(title))))
    return items

def main():
    docx_files = sorted(list(DOCX_ROOT.rglob("*.docx")))
    md_items = collect_md_items()
    
    unconverted = []
    for docx in docx_files:
        dn = norm_title(docx.stem)
        matched_item = None
        for it in md_items:
            if it.norm and dn and (it.norm in dn or dn in it.norm):
                matched_item = it
                break
        
        if not matched_item:
            unconverted.append(docx)
            print(f"[MISSING] {docx.name}")
        # else:
        #     print(f"[MATCHED] {docx.name} -> {matched_item.folder_name}")

    if not unconverted:
        print("All DOCX files appear to be converted.")
    else:
        print(f"\nTotal missing: {len(unconverted)}")

if __name__ == "__main__":
    main()
