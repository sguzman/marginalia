#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCX_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "docx"
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"
TEMPLATE_YAML = MD_ROOT / "template.yaml"


def die(message: str, *, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


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


def slugify(s: str) -> str:
    s = s.lower()
    s = (
        s.replace("—", "-")
        .replace("–", "-")
        .replace("‑", "-")
        .replace("“", "")
        .replace("”", "")
        .replace("’", "")
        .replace("‘", "")
    )
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "doc"


def load_yaml_first_doc(path: Path) -> dict[str, Any]:
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    for doc in docs:
        if isinstance(doc, dict) and doc:
            return doc
    return {}


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        default_flow_style=False,
    )


def read_h1_from_text(text: str) -> str | None:
    for line in text.splitlines()[:12]:
        if line.startswith("# "):
            return line[2:].strip()
    return None


def read_h1(path: Path) -> str | None:
    return read_h1_from_text(path.read_text(encoding="utf-8"))


def ensure_h1_first(md_text: str, title: str) -> str:
    lines = md_text.lstrip("\ufeff").splitlines()
    if lines and lines[0].startswith("# "):
        return md_text if md_text.endswith("\n") else md_text + "\n"
    title = title.strip() or "Untitled"
    out = "# " + title + "\n\n" + md_text.lstrip("\n")
    return out if out.endswith("\n") else out + "\n"


def cleanup_pandoc_md(md_text: str) -> str:
    # Remove common pandoc image size attrs: ![](x){width=".." height=".."}
    md_text = re.sub(r"\)\{[^}]*\}", ")", md_text)
    # Remove common LLM refusal boilerplate if it appears right after the title.
    md_text = re.sub(
        r"(?ms)^(# .+?\n+)"
        r"(?:I['’]m sorry, but I cannot.*?\n(?:\s*\n|$))",
        r"\1",
        md_text,
    )
    # Collapse extreme blank runs
    md_text = re.sub(r"\n{4,}", "\n\n\n", md_text)
    return md_text if md_text.endswith("\n") else md_text + "\n"


def shorten_for_description(s: str, max_len: int = 240) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def extract_docx_core_props(docx_path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    try:
        with zipfile.ZipFile(docx_path) as zf:
            xml = zf.read("docProps/core.xml").decode("utf-8", errors="replace")
    except Exception:
        return props

    def grab(tag: str) -> str | None:
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml, flags=re.DOTALL)
        if not m:
            return None
        raw = re.sub(r"\s+", " ", m.group(1)).strip()
        raw = raw.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return raw

    for k, tag in [
        ("title", "dc:title"),
        ("created", "dcterms:created"),
        ("modified", "dcterms:modified"),
        ("creator", "dc:creator"),
        ("description", "dc:description"),
    ]:
        v = grab(tag)
        if v:
            props[k] = v

    return props


def parse_docx_date(props: dict[str, str], docx_path: Path) -> str:
    for key in ("modified", "created"):
        v = props.get(key)
        if not v:
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", v)
        if m:
            return m.group(1)

    ts = docx_path.stat().st_mtime
    return dt.date.fromtimestamp(ts).isoformat()


@dataclass(frozen=True)
class MdItem:
    name: str
    title: str
    norm: str


def collect_md_items() -> list[MdItem]:
    items: list[MdItem] = []

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
            items.append(MdItem(name=d.name, title=str(title), norm=norm_title(str(title))))

    for p in sorted(MD_ROOT.glob("*.md")):
        title = read_h1(p)
        if title:
            items.append(MdItem(name=p.stem, title=title, norm=norm_title(title)))

    return items


def docx_missing_conversions(docx_files: list[Path], md_items: list[MdItem]) -> list[Path]:
    missing: list[Path] = []
    for p in docx_files:
        dn = norm_title(p.stem)
        matched = False
        for it in md_items:
            if it.norm and dn and (it.norm in dn or dn in it.norm):
                matched = True
                break
        if not matched:
            missing.append(p)
    return missing


def pandoc_to_gfm(docx_path: Path, out_md: Path, extract_media_dir: Path) -> None:
    extract_media_dir.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(docx_path),
        "-t",
        "gfm+tex_math_dollars+pipe_tables+task_lists",
        "--wrap=none",
        f"--extract-media={extract_media_dir}",
        "-o",
        str(out_md),
    ]
    subprocess.run(cmd, check=True)


def first_paragraph(md_text: str) -> str | None:
    lines = md_text.splitlines()
    idx = 0
    if lines and lines[0].startswith("# "):
        idx = 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1

    para: list[str] = []
    while idx < len(lines):
        line = lines[idx].rstrip()
        if not line.strip():
            break
        if line.startswith("#"):
            break
        if line.strip().startswith("![](") or line.strip().startswith("!["):
            idx += 1
            continue
        para.append(line)
        idx += 1

    out = " ".join(para).strip()
    return out or None


def build_article_yaml(
    *,
    template: dict[str, Any],
    title: str,
    slug: str,
    date: str,
    description: str,
    abstract: str,
    docx_filename: str,
    pandoc_version: str,
    conversion_date: str,
) -> dict[str, Any]:
    data: dict[str, Any] = dict(template)

    data["title"] = title
    data["slug"] = slug
    data["date"] = date
    data["description"] = description
    data["abstract"] = abstract
    data["author"] = ["Salvador Guzman"]
    data["creator"] = ["Salvador Guzman"]
    data["publisher"] = "Marginalia"
    data["license"] = "CC0-1.0"
    data["rights"] = "CC0-1.0"
    data["format"] = "markdown"
    data["draft"] = False

    for key in ("keywords", "categories", "subject", "subjects"):
        if key not in data or data[key] is None:
            data[key] = []

    report = data.get("report")
    if not isinstance(report, dict):
        report = {}
    report["conversion"] = {
        "source_docx": docx_filename,
        "tool": f"pandoc {pandoc_version}",
        "date": conversion_date,
    }
    data["report"] = report

    return data


def fix_report_h1_from_metadata(folder: Path) -> bool:
    meta_path = folder / "article.yaml"
    md_path = folder / "main.md"
    if not meta_path.exists() or not md_path.exists():
        return False
    meta = load_yaml_first_doc(meta_path)
    title = meta.get("title") or read_h1(md_path) or folder.name
    md_text = md_path.read_text(encoding="utf-8")
    new_text = ensure_h1_first(md_text, str(title))
    if new_text != md_text:
        md_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def fix_html_history_title() -> bool:
    folder = MD_ROOT / "html-history"
    meta_path = folder / "article.yaml"
    md_path = folder / "main.md"
    if not meta_path.exists() or not md_path.exists():
        return False

    meta_txt = meta_path.read_text(encoding="utf-8")
    docs = list(yaml.safe_load_all(meta_txt))
    meta = None
    for doc in docs:
        if isinstance(doc, dict) and doc:
            meta = doc
            break
    if not meta:
        return False

    if meta.get("title"):
        return False

    title = read_h1(md_path) or "History of HTML"
    meta["title"] = title
    meta_path.write_text("---\n" + dump_yaml(meta) + "...\n", encoding="utf-8")
    return True


def move_standalone_md(stem: str) -> bool:
    src = MD_ROOT / f"{stem}.md"
    if not src.exists():
        return False

    text = src.read_text(encoding="utf-8")
    title = read_h1_from_text(text) or stem.replace("-", " ").title()
    folder = MD_ROOT / slugify(stem)
    main_md = folder / "main.md"
    meta_yaml = folder / "article.yaml"

    if folder.exists():
        src.unlink()
        return True

    folder.mkdir(parents=True, exist_ok=True)
    main_md.write_text(ensure_h1_first(text, title), encoding="utf-8")

    props_date = dt.date.fromtimestamp(src.stat().st_mtime).isoformat()
    template = load_yaml_first_doc(TEMPLATE_YAML)
    desc = shorten_for_description(first_paragraph(text) or title)
    abstract = shorten_for_description(first_paragraph(text) or title, max_len=800)
    pandoc_version = subprocess.check_output(["pandoc", "-v"], text=True).splitlines()[0].strip().removeprefix("pandoc ")
    conversion_date = dt.date.today().isoformat()

    article = build_article_yaml(
        template=template,
        title=title,
        slug=folder.name,
        date=props_date,
        description=desc,
        abstract=abstract,
        docx_filename="(standalone-md)",
        pandoc_version=pandoc_version,
        conversion_date=conversion_date,
    )
    meta_yaml.write_text("---\n" + dump_yaml(article) + "...\n", encoding="utf-8")

    src.unlink()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ai_reports_sync.py",
        description="Convert missing DOCX reports to MD + generate article.yaml, and clean up known issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python scripts/ai_reports_sync.py
              python scripts/ai_reports_sync.py --limit 5
            """
        ).strip(),
    )
    parser.add_argument("--limit", type=int, default=0, help="Process at most N missing docx conversions (0 = all).")
    args = parser.parse_args()

    if not DOCX_ROOT.exists():
        die(f"missing {DOCX_ROOT}")
    if not MD_ROOT.exists():
        die(f"missing {MD_ROOT}")
    if not TEMPLATE_YAML.exists():
        die(f"missing {TEMPLATE_YAML}")

    template = load_yaml_first_doc(TEMPLATE_YAML)
    if not template:
        die(f"failed to parse template: {TEMPLATE_YAML}")

    pandoc_version = subprocess.check_output(["pandoc", "-v"], text=True).splitlines()[0].strip().removeprefix("pandoc ")
    conversion_date = dt.date.today().isoformat()

    docx_files = sorted(DOCX_ROOT.rglob("*.docx"))
    md_items = collect_md_items()
    missing = docx_missing_conversions(docx_files, md_items)

    existing_slugs = {p.name for p in MD_ROOT.iterdir() if p.is_dir()}
    created = 0

    to_process = missing[: (args.limit or None)]
    for docx in to_process:
        base_slug = slugify(docx.stem)
        slug = base_slug
        i = 2
        while slug in existing_slugs:
            slug = f"{base_slug}-{i}"
            i += 1
        existing_slugs.add(slug)

        out_dir = MD_ROOT / slug
        out_md = out_dir / "main.md"
        out_meta = out_dir / "article.yaml"
        out_assets = out_dir / "assets"

        if out_md.exists() and out_meta.exists():
            continue

        props = extract_docx_core_props(docx)
        title = props.get("title") or docx.stem
        date = parse_docx_date(props, docx)

        pandoc_to_gfm(docx, out_md, out_assets)
        md_text = cleanup_pandoc_md(out_md.read_text(encoding="utf-8"))
        md_text = ensure_h1_first(md_text, title)
        out_md.write_text(md_text, encoding="utf-8")

        desc = shorten_for_description(first_paragraph(md_text) or title)
        abstract = shorten_for_description(first_paragraph(md_text) or title, max_len=800)

        article = build_article_yaml(
            template=template,
            title=title,
            slug=slug,
            date=date,
            description=desc,
            abstract=abstract,
            docx_filename=docx.name,
            pandoc_version=pandoc_version,
            conversion_date=conversion_date,
        )
        out_meta.write_text("---\n" + dump_yaml(article) + "...\n", encoding="utf-8")
        created += 1

    dirty_h1 = [
        "2christian-socialism",
        "3mutualism",
        "category-theory",
        "hasan",
        "marx-engels",
        "marxism-evolution",
    ]
    fixed_h1 = sum(1 for name in dirty_h1 if fix_report_h1_from_metadata(MD_ROOT / name))

    male_fixed = 0
    male_folder = MD_ROOT / "male-suicide"
    male_docx = DOCX_ROOT / "Male Suicide Research Outline.docx"
    if male_folder.exists() and male_docx.exists():
        out_md = male_folder / "main.md"
        out_assets = male_folder / "assets"
        pandoc_to_gfm(male_docx, out_md, out_assets)
        md_text = cleanup_pandoc_md(out_md.read_text(encoding="utf-8"))
        title = load_yaml_first_doc(male_folder / "article.yaml").get("title") or male_docx.stem
        out_md.write_text(ensure_h1_first(md_text, str(title)), encoding="utf-8")
        male_fixed = 1

    gaht_fixed = 0
    gaht_folder = MD_ROOT / "gaht"
    gaht_docx = DOCX_ROOT / "GAHT Research Report Summary.docx"
    if gaht_folder.exists() and gaht_docx.exists():
        out_md = gaht_folder / "main.md"
        out_assets = gaht_folder / "assets"
        pandoc_to_gfm(gaht_docx, out_md, out_assets)
        md_text = cleanup_pandoc_md(out_md.read_text(encoding="utf-8"))
        title = load_yaml_first_doc(gaht_folder / "article.yaml").get("title") or gaht_docx.stem
        out_md.write_text(ensure_h1_first(md_text, str(title)), encoding="utf-8")
        gaht_fixed = 1

    html_fixed = 1 if fix_html_history_title() else 0

    moved_standalone = 0
    moved_standalone += 1 if move_standalone_md("culture-gothic") else 0
    moved_standalone += 1 if move_standalone_md("nietzche-math-critique") else 0

    print(
        "\n".join(
            [
                f"docx_total={len(docx_files)}",
                f"md_items={len(md_items)}",
                f"missing_docx={len(missing)}",
                f"created_new_md={created}",
                f"fixed_h1_only={fixed_h1}",
                f"male_suicide_reconverted={male_fixed}",
                f"gaht_reconverted={gaht_fixed}",
                f"html_history_title_fixed={html_fixed}",
                f"standalone_md_moved={moved_standalone}",
            ]
        )
    )


if __name__ == "__main__":
    main()
