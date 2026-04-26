#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MD_ROOT = REPO_ROOT / "tmp" / "ai-research-reports" / "data" / "md"
POSTS_DIR = REPO_ROOT / "content" / "posts"
DATA_DIR = REPO_ROOT / "data" / "ai"
ARTICLES_YAML = DATA_DIR / "articles.yaml"


class FoldedStr(str):
    pass


def _represent_folded_str(dumper: yaml.Dumper, data: FoldedStr) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=">")


yaml.SafeDumper.add_representer(FoldedStr, _represent_folded_str)


def die(message: str, *, code: int = 1) -> None:
    raise SystemExit(f"error: {message}")


def load_yaml_first_doc(path: Path) -> dict[str, Any]:
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    for doc in docs:
        if isinstance(doc, dict) and doc:
            return doc
    return {}


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
        default_flow_style=False,
    )


def read_h1_from_text(text: str) -> str | None:
    for line in text.splitlines()[:20]:
        if line.startswith("# "):
            return line[2:].strip()
    return None


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


def strip_markdown(s: str) -> str:
    # Replace markdown links [text](url) -> text
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    # Drop common escaped citation markers like [\[1\]] that show up after pandoc conversions.
    s = re.sub(r"\[\\\[\d+\\\]\]", "", s)
    # Remove emphasis/code markers.
    s = s.replace("**", "").replace("*", "").replace("`", "")
    # Remove stray backslashes (often used as hard-break markers).
    s = s.replace("\\", "")
    return s


def shorten(s: str, *, max_len: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    # Remove a common pandoc/authoring pattern that breaks YAML when dumped as a quoted scalar.
    s = re.sub(r"\*\*Executive Summary\*\*\\\s*", "Executive Summary: ", s)
    s = re.sub(r"\*\*Executive Summary\*\*\s*", "Executive Summary: ", s)
    s = strip_markdown(s)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def strip_leading_h1(md_text: str) -> str:
    lines = md_text.lstrip("\ufeff").splitlines()
    if not lines:
        return ""
    if not lines[0].startswith("# "):
        return md_text if md_text.endswith("\n") else md_text + "\n"
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    out = "\n".join(lines[i:]).lstrip("\n")
    return out if out.endswith("\n") else out + "\n"


def normalize_title(title: str) -> str:
    title = title.strip()
    title = title.replace("_", ": ")
    title = re.sub(r"\s*:\s*", ": ", title)
    title = re.sub(r"\s{2,}", " ", title)
    title = title.replace("“", "“").replace("”", "”")  # no-op; keeps unicode quotes
    title = title.replace(" / ", " / ")
    title = title.replace("—", "—")
    return title


def prefer_h1_title(meta_title: str | None, h1_title: str | None, fallback: str) -> str:
    title = (h1_title or meta_title or fallback).strip()
    title = normalize_title(title)
    return title or fallback


def assets_file_count(folder: Path) -> int:
    assets = folder / "assets"
    if not assets.exists():
        return 0
    return sum(1 for p in assets.rglob("*") if p.is_file())


@dataclass(frozen=True)
class Article:
    slug: str
    folder: Path
    meta_path: Path
    md_path: Path
    meta: dict[str, Any]
    md_text: str

    @property
    def h1(self) -> str | None:
        return read_h1_from_text(self.md_text)

    @property
    def title(self) -> str:
        return prefer_h1_title(
            str(self.meta.get("title")) if self.meta.get("title") else None,
            self.h1,
            self.slug.replace("-", " ").title(),
        )

    @property
    def date(self) -> str:
        raw = self.meta.get("date")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        # last resort: folder mtime
        return dt.date.fromtimestamp(self.folder.stat().st_mtime).isoformat()

    @property
    def description(self) -> str:
        para = first_paragraph(self.md_text) or self.title
        return shorten(para, max_len=240)

    @property
    def abstract(self) -> str:
        para = first_paragraph(self.md_text) or self.title
        return shorten(para, max_len=800)


def collect_articles() -> list[Article]:
    if not MD_ROOT.exists():
        die(f"missing md root: {MD_ROOT}")

    articles: list[Article] = []
    for folder in sorted([p for p in MD_ROOT.iterdir() if p.is_dir()]):
        meta_path = folder / "article.yaml"
        md_path = folder / "main.md"
        if not meta_path.exists() or not md_path.exists():
            continue
        meta = load_yaml_first_doc(meta_path)
        md_text = md_path.read_text(encoding="utf-8")
        articles.append(
            Article(
                slug=folder.name,
                folder=folder,
                meta_path=meta_path,
                md_path=md_path,
                meta=meta,
                md_text=md_text,
            )
        )
    return articles


def fix_article_yaml(a: Article) -> bool:
    new = dict(a.meta)
    changed = False

    if new.get("slug") != a.slug:
        new["slug"] = a.slug
        changed = True

    if new.get("title") != a.title:
        new["title"] = a.title
        changed = True

    if new.get("description") != a.description:
        new["description"] = a.description
        changed = True

    if new.get("abstract") != a.abstract:
        new["abstract"] = a.abstract
        changed = True

    # Keep these sane for blog publishing
    if new.get("draft") is not False:
        new["draft"] = False
        changed = True

    if changed:
        a.meta_path.write_text("---\n" + dump_yaml(new) + "...\n", encoding="utf-8")
    return changed


def hugo_frontmatter_from_article(a: Article) -> dict[str, Any]:
    meta = dict(a.meta)
    meta.setdefault("abstract", a.abstract)
    meta.setdefault("creator", ["Salvador Guzman"])
    meta.setdefault("publisher", "Marginalia")
    meta.setdefault("license", "CC0-1.0")
    meta.setdefault("rights", "CC0-1.0")
    meta.setdefault("language", meta.get("lang") or "en")
    meta.setdefault("identifier", a.slug)

    authors = meta.get("author")
    if isinstance(authors, str):
        authors_list = [authors]
    elif isinstance(authors, list):
        authors_list = [str(x) for x in authors if str(x).strip()]
    else:
        authors_list = ["Salvador Guzman"]

    # Heuristic: if pandoc conversion exists, include ChatGPT as co-author in the blog view.
    conversion = (
        meta.get("report", {}) if isinstance(meta.get("report"), dict) else {}
    ).get("conversion")
    if isinstance(conversion, dict) and conversion.get("source_docx") not in {None, "", "(standalone-md)"}:
        if "ChatGPT" not in authors_list:
            authors_list.append("ChatGPT")

    categories = meta.get("categories") if isinstance(meta.get("categories"), list) else []
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    keywords = meta.get("keywords") if isinstance(meta.get("keywords"), list) else []

    return {
        "title": a.title,
        "linkTitle": a.title if len(a.title) <= 60 else a.title[:57].rstrip() + "…",
        "description": FoldedStr(a.description),
        "summary": FoldedStr(str(meta.get("abstract") or a.abstract)),
        "slug": a.slug,
        "url": "",
        "aliases": [],
        "date": a.date,
        "lastmod": dt.date.today().isoformat(),
        "draft": False,
        "authors": authors_list,
        "layout": "single",
        "weight": 0,
        "categories": categories,
        "tags": tags,
        "keywords": keywords,
        "markup": "goldmark",
        "outputs": ["HTML", "RSS"],
        "meta": meta,
    }


def write_post(a: Article, *, dry_run: bool) -> tuple[Path, bool]:
    fm = hugo_frontmatter_from_article(a)
    body = strip_leading_h1(a.md_text)

    assets_count = assets_file_count(a.folder)
    if assets_count > 0:
        target_dir = POSTS_DIR / a.slug
        target_md = target_dir / "index.md"
    else:
        target_md = POSTS_DIR / f"{a.slug}.md"
        target_dir = None

    out = "---\n" + dump_yaml(fm) + "---\n\n" + body

    if dry_run:
        return target_md, False

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    if target_dir:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Copy assets as-is so pandoc relative links keep working.
        src_assets = a.folder / "assets"
        if src_assets.exists():
            dst_assets = target_dir / "assets"
            dst_assets.mkdir(parents=True, exist_ok=True)
            # Shallow-ish copy: only files, preserves subdirs
            for src in src_assets.rglob("*"):
                if src.is_dir():
                    continue
                rel = src.relative_to(src_assets)
                dst = dst_assets / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
        # If a leaf post exists, remove it to avoid duplicates.
        leaf = POSTS_DIR / f"{a.slug}.md"
        if leaf.exists():
            leaf.unlink()
    else:
        # If a bundle exists from earlier runs, remove it to avoid duplicates.
        bundle = POSTS_DIR / a.slug
        if bundle.exists() and bundle.is_dir():
            for p in sorted(bundle.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            bundle.rmdir()

    prior = target_md.read_text(encoding="utf-8") if target_md.exists() else None
    if prior != out:
        target_md.write_text(out, encoding="utf-8")
        return target_md, True
    return target_md, False


def write_articles_yaml(articles: list[Article], *, dry_run: bool) -> bool:
    rows: list[dict[str, Any]] = []
    posts = {p.stem: p for p in POSTS_DIR.glob("*.md")}
    bundles = {p.name: p for p in POSTS_DIR.iterdir() if p.is_dir()}

    for a in articles:
        published = a.slug in posts or a.slug in bundles
        assets_count = assets_file_count(a.folder)
        rows.append(
            {
                "slug": a.slug,
                "title": a.title,
                "date": a.date,
                "description": a.description,
                "source": (
                    "docx"
                    if (
                        isinstance(a.meta.get("report"), dict)
                        and isinstance(a.meta["report"].get("conversion"), dict)
                        and a.meta["report"]["conversion"].get("source_docx")
                        not in {None, "", "(standalone-md)"}
                    )
                    else "md"
                ),
                "md_path": str(a.md_path.relative_to(REPO_ROOT)),
                "meta_path": str(a.meta_path.relative_to(REPO_ROOT)),
                "assets_files": assets_count,
                "published": published,
            }
        )

    payload = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(), "articles": rows}
    out = dump_yaml(payload)
    if dry_run:
        return False
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prior = ARTICLES_YAML.read_text(encoding="utf-8") if ARTICLES_YAML.exists() else None
    if prior != out:
        ARTICLES_YAML.write_text(out, encoding="utf-8")
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="ai_reports_publish.py",
        description="Fix md/article.yaml metadata, generate a single articles.yaml, and publish to Hugo posts.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Don't write files.")
    ap.add_argument("--no-publish", action="store_true", help="Don't write into content/posts.")
    args = ap.parse_args()

    articles = collect_articles()
    if not articles:
        die(f"no articles found under {MD_ROOT}")

    fixed_meta = 0
    for a in articles:
        fixed_meta += 1 if fix_article_yaml(a) else 0

    articles = collect_articles()  # reload after fixes
    wrote_articles = write_articles_yaml(articles, dry_run=args.dry_run)

    wrote_posts = 0
    if not args.no_publish:
        for a in articles:
            _, changed = write_post(a, dry_run=args.dry_run)
            wrote_posts += 1 if changed else 0

    print(
        "\n".join(
            [
                f"articles={len(articles)}",
                f"fixed_article_yaml={fixed_meta}",
                f"wrote_articles_yaml={int(wrote_articles)}",
                f"wrote_posts={wrote_posts}",
            ]
        )
    )


if __name__ == "__main__":
    main()
