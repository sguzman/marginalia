import yaml
from pathlib import Path

MD_ROOT = Path("/win/linux/Code/Text/marginalia/tmp/ai-research-reports/data/md")

def needs_enrichment(meta_path: Path):
    try:
        docs = list(yaml.safe_load_all(meta_path.read_text(encoding="utf-8")))
        for doc in docs:
            if isinstance(doc, dict) and doc:
                # If tags or categories are empty, or abstract is just the title
                tags = doc.get("tags", [])
                cats = doc.get("categories", [])
                abstract = doc.get("abstract", "")
                title = doc.get("title", "")
                
                if not tags or not cats or abstract == title:
                    return True
    except:
        return True
    return False

def main():
    folders = sorted([d for d in MD_ROOT.iterdir() if d.is_dir()])
    sparse = []
    for d in folders:
        meta_path = d / "article.yaml"
        if meta_path.exists() and needs_enrichment(meta_path):
            sparse.append(d.name)
    
    for s in sparse:
        print(s)

if __name__ == "__main__":
    main()
