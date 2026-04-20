import os
import yaml
from pathlib import Path

REPO_ROOT = Path("/win/linux/Code/Text/marginalia")
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"

REQUIRED_FIELDS = ["title", "slug", "date"]
RECOMMENDED_FIELDS = ["categories", "tags", "description", "abstract"]

def load_yaml(path: Path):
    try:
        docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        for doc in docs:
            if isinstance(doc, dict) and doc:
                return doc
    except:
        pass
    return None

def main():
    folders = sorted([d for d in MD_ROOT.iterdir() if d.is_dir()])
    
    results = []
    for d in folders:
        meta_path = d / "article.yaml"
        md_path = d / "main.md"
        
        status = {
            "folder": d.name,
            "has_meta": meta_path.exists(),
            "has_md": md_path.exists(),
            "md_size": md_path.stat().st_size if md_path.exists() else 0,
            "meta_keys": 0,
            "missing_required": [],
            "missing_recommended": []
        }
        
        if meta_path.exists():
            meta = load_yaml(meta_path)
            if meta:
                status["meta_keys"] = len(meta)
                for f in REQUIRED_FIELDS:
                    if f not in meta or not meta[f]:
                        status["missing_required"].append(f)
                for f in RECOMMENDED_FIELDS:
                    if f not in meta or not meta[f]:
                        # Check subjects/subject for tags/categories
                        if f == "tags" and "tags" not in meta and "keywords" not in meta:
                            status["missing_recommended"].append(f)
                        elif f == "categories" and "categories" not in meta:
                            status["missing_recommended"].append(f)
                        elif f == "description" and "description" not in meta:
                            status["missing_recommended"].append(f)
                        elif f == "abstract" and "abstract" not in meta:
                            status["missing_recommended"].append(f)
            else:
                status["has_meta"] = "invalid"

        results.append(status)

    # Summary
    print(f"Total folders checked: {len(results)}")
    
    missing_md = [r for r in results if not r["has_md"] or r["md_size"] == 0]
    invalid_meta = [r for r in results if r["has_meta"] == "invalid" or not r["has_meta"]]
    low_key_count = [r for r in results if r["meta_keys"] < 10]
    missing_req = [r for r in results if r["missing_required"]]
    
    print(f"Folders missing or empty main.md: {len(missing_md)}")
    print(f"Folders missing or invalid article.yaml: {len(invalid_meta)}")
    print(f"Folders with fewer than 10 metadata keys: {len(low_key_count)}")
    print(f"Folders missing required fields (title, slug, date): {len(missing_req)}")
    
    if missing_md or invalid_meta or missing_req:
        print("\nISSUES FOUND:")
        for r in results:
            if r in missing_md or r in invalid_meta or r in missing_req:
                print(f"  - {r['folder']}: MD:{r['has_md']} ({r['md_size']} bytes), Meta Keys:{r['meta_keys']}, Missing Req:{r['missing_required']}")
    else:
        print("\nAll folders have a non-empty main.md and a rich article.yaml (avg keys: {:.1f})".format(
            sum(r["meta_keys"] for r in results) / len(results)
        ))

if __name__ == "__main__":
    main()
