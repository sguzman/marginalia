#!/usr/bin/env python3
"""Publish canonical ai-research-reports packages into Hugo.

The source repository is read-only. This tool never changes source metadata or
publication state. It also refuses to overwrite an existing unmanaged blog post.
Default mode is a dry run. Pass --write to create or update managed posts.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
POSTS_ROOT = REPO_ROOT / "content" / "posts"
ELIGIBLE_STATUSES = {"ready", "published"}
MANAGED_BY = "ai-research-reports"


def load_yaml(path: Path) -> dict[str, Any]:
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    for doc in docs:
        if isinstance(doc, dict):
            return doc
    raise ValueError(f"no YAML mapping found in {path}")


def dump_yaml(value: Any) -> str:
    return yaml.safe_dump(
        value,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
        default_flow_style=False,
    )


def clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def strip_leading_h1(text: str) -> str:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines:
        return ""
    if lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).rstrip() + "\n"


def package_digest(meta_bytes: bytes, body_bytes: bytes) -> str:
    h = hashlib.sha256()
    h.update(meta_bytes)
    h.update(b"\0")
    h.update(body_bytes)
    return h.hexdigest()


def managed_frontmatter(*, slug: str, meta: dict[str, Any], digest: str) -> dict[str, Any]:
    title = clean_text(meta.get("title"))
    description = clean_text(meta.get("description")) or clean_text(meta.get("summary")) or title
    summary = clean_text(meta.get("summary")) or clean_text(meta.get("abstract")) or description
    date = clean_text(meta.get("date"))
    lastmod = clean_text(meta.get("lastmod")) or date

    if not title or not date:
        raise ValueError("canonical metadata must contain nonblank title and date")

    authors = meta.get("authors") or meta.get("author") or ["Salvador Guzman", "ChatGPT"]
    if isinstance(authors, str):
        authors = [authors]
    if not isinstance(authors, list):
        raise ValueError("authors/author must be a list or string")

    return {
        "title": title,
        "linkTitle": clean_text(meta.get("linkTitle")) or title,
        "description": description,
        "summary": summary,
        "date": date,
        "lastmod": lastmod,
        "draft": False,
        "slug": slug,
        "authors": [str(x) for x in authors],
        "categories": meta.get("categories") if isinstance(meta.get("categories"), list) else [],
        "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
        "keywords": meta.get("keywords") if isinstance(meta.get("keywords"), list) else [],
        "layout": "single",
        "markup": "goldmark",
        "outputs": ["HTML", "RSS"],
        "ai_generated": "ChatGPT" in [str(x) for x in authors],
        "managed_by": MANAGED_BY,
        "source_repo": "sguzman/ai-research-reports",
        "source_path": f"data/md/{slug}",
        "source_digest": digest,
        "meta": meta,
    }


def split_frontmatter(text: str) -> tuple[dict[str, Any], str] | None:
    if not text.startswith("---\n"):
        return None
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end < 0:
        return None
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        return None
    return data, text[end + len(marker) :]


def target_for(slug: str, source_assets: Path) -> tuple[Path, Path | None]:
    has_assets = source_assets.is_dir() and any(p.is_file() for p in source_assets.rglob("*"))
    if has_assets:
        bundle = POSTS_ROOT / slug
        return bundle / "index.md", bundle
    return POSTS_ROOT / f"{slug}.md", None


def assert_target_is_managed(target: Path) -> None:
    candidates = [target]
    if target.name == "index.md":
        candidates.append(POSTS_ROOT / f"{target.parent.name}.md")
    else:
        candidates.append(POSTS_ROOT / target.stem / "index.md")

    existing = next((path for path in candidates if path.exists()), None)
    if existing is None:
        return
    parsed = split_frontmatter(existing.read_text(encoding="utf-8", errors="replace"))
    if not parsed or parsed[0].get("managed_by") != MANAGED_BY:
        raise FileExistsError(f"refusing to overwrite unmanaged post: {existing}")


def publish_one(source_root: Path, slug: str, *, write: bool) -> bool:
    folder = source_root / "data" / "md" / slug
    meta_path = folder / "article.yaml"
    body_path = folder / "main.md"
    if not meta_path.is_file() or not body_path.is_file():
        raise FileNotFoundError(f"incomplete canonical package: {folder}")

    meta_bytes = meta_path.read_bytes()
    body_bytes = body_path.read_bytes()
    meta = load_yaml(meta_path)
    body = body_bytes.decode("utf-8")

    if clean_text(meta.get("slug")) != slug:
        raise ValueError(f"{slug}: metadata slug does not match folder")
    status = clean_text(meta.get("status")).lower()
    if status not in ELIGIBLE_STATUSES:
        raise ValueError(f"{slug}: status {status!r} is not publishable")
    if meta.get("draft") is not False:
        raise ValueError(f"{slug}: eligible publication requires draft: false")

    digest = package_digest(meta_bytes, body_bytes)
    fm = managed_frontmatter(slug=slug, meta=meta, digest=digest)
    output = "---\n" + dump_yaml(fm) + "---\n\n" + strip_leading_h1(body)

    source_assets = folder / "assets"
    target, bundle = target_for(slug, source_assets)
    assert_target_is_managed(target)

    prior = target.read_text(encoding="utf-8") if target.exists() else None
    changed = prior != output
    mode = "WRITE" if write else "DRY-RUN"
    state = "changed" if changed else "unchanged"
    print(f"{mode} {slug}: {state} -> {target.relative_to(REPO_ROOT)}")

    if not write or not changed:
        return changed

    POSTS_ROOT.mkdir(parents=True, exist_ok=True)
    if bundle is not None:
        bundle.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="utf-8")
        if source_assets.is_dir():
            destination = bundle / "assets"
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source_assets, destination)
    else:
        target.write_text(output, encoding="utf-8")
    return True


def discover_eligible(source_root: Path) -> list[str]:
    md_root = source_root / "data" / "md"
    slugs: list[str] = []
    for folder in sorted(p for p in md_root.iterdir() if p.is_dir()):
        meta_path = folder / "article.yaml"
        body_path = folder / "main.md"
        if not meta_path.is_file() or not body_path.is_file():
            continue
        try:
            meta = load_yaml(meta_path)
        except Exception:
            continue
        if clean_text(meta.get("status")).lower() in ELIGIBLE_STATUSES and meta.get("draft") is False:
            slugs.append(folder.name)
    return slugs


def main() -> int:
    parser = argparse.ArgumentParser(description="One-way publisher from ai-research-reports to Marginalia.")
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="path to a checkout of sguzman/ai-research-reports",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug", help="publish one canonical slug")
    group.add_argument("--all", action="store_true", help="publish every eligible canonical slug")
    parser.add_argument("--write", action="store_true", help="write changes; default is dry-run")
    args = parser.parse_args()

    source_root = args.source.resolve()
    if not (source_root / "data" / "md").is_dir():
        print(f"error: not an ai-research-reports checkout: {source_root}", file=sys.stderr)
        return 2

    slugs = [args.slug] if args.slug else discover_eligible(source_root)
    changed = 0
    try:
        for slug in slugs:
            changed += int(publish_one(source_root, slug, write=args.write))
    except (FileNotFoundError, FileExistsError, ValueError, UnicodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"articles={len(slugs)} changed={changed} mode={'write' if args.write else 'dry-run'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
