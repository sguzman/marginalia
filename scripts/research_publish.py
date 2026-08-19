#!/usr/bin/env python3
"""Publish canonical ai-research-reports packages into Hugo.

The source repository is read-only. This tool never changes source metadata or
publication state. It also refuses to overwrite an existing unmanaged blog post.
Default mode is a dry run. Pass --write to create or update managed posts.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
POSTS_ROOT = REPO_ROOT / "content" / "posts"
ELIGIBLE_STATUSES = {"ready", "published"}
MANAGED_BY = "ai-research-reports"

MARKDOWN_TARGET_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\n]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.I)
HTML_LINK_RE = re.compile(r"<a\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.I)
MERMAID_BLOCK_RE = re.compile(r"(?ms)^```mermaid\s*\n.*?^```\s*$")
UNFENCED_DIAGRAM_RE = re.compile(
    r"(?m)^(?: {4}|\t)(?:flowchart|graph|sequenceDiagram|classDiagram|"
    r"stateDiagram(?:-v2)?|erDiagram|gantt|pie|journey|mindmap|timeline)\b"
)


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


def iter_asset_files(assets_root: Path) -> list[Path]:
    if not assets_root.is_dir():
        return []
    return sorted(p for p in assets_root.rglob("*") if p.is_file())


def package_digest(meta_bytes: bytes, body_bytes: bytes, assets_root: Path) -> str:
    """Hash canonical metadata, body, asset names, and asset contents."""
    h = hashlib.sha256()
    h.update(meta_bytes)
    h.update(b"\0body\0")
    h.update(body_bytes)

    for path in iter_asset_files(assets_root):
        relative = path.relative_to(assets_root).as_posix().encode("utf-8")
        h.update(b"\0asset\0")
        h.update(relative)
        h.update(b"\0")
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                h.update(chunk)
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


def parse_local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()

    if " " in target and not target.startswith(("http://", "https://")):
        target = target.split(None, 1)[0]

    parsed = urlsplit(target)
    if parsed.scheme or target.startswith(("#", "//")):
        return None
    return unquote(parsed.path) or None


def validate_source_integrity(folder: Path, body: str) -> None:
    """Fail closed on local dependencies the publication layer cannot reproduce."""
    assets_root = (folder / "assets").resolve()

    def validate_target(kind: str, raw_target: str) -> None:
        local = parse_local_target(raw_target)
        if local is None:
            return

        resolved = (folder / local).resolve()
        try:
            resolved.relative_to(assets_root)
        except ValueError as exc:
            raise ValueError(
                f"{folder.name}: {kind} must resolve beneath assets/: {raw_target!r}"
            ) from exc

        if not resolved.is_file():
            raise ValueError(
                f"{folder.name}: missing local {kind} target: {raw_target!r}"
            )

    for match in MARKDOWN_TARGET_RE.finditer(body):
        kind = "image" if match.group(1) else "file link"
        validate_target(kind, match.group(3).strip())

    for match in HTML_IMG_RE.finditer(body):
        validate_target("HTML image", match.group(1).strip())

    for match in HTML_LINK_RE.finditer(body):
        validate_target("HTML file link", match.group(1).strip())

    if MERMAID_BLOCK_RE.search(body) or UNFENCED_DIAGRAM_RE.search(body):
        raise ValueError(
            f"{folder.name}: publishable source contains Mermaid/diagram source, "
            "but Marginalia has no Mermaid renderer; publish a rendered asset instead"
        )

    if body.count("```") % 2:
        raise ValueError(
            f"{folder.name}: unmatched triple-backtick fence; refusing potentially broken rendering"
        )


def target_for(slug: str, source_assets: Path) -> tuple[Path, Path | None]:
    has_assets = bool(iter_asset_files(source_assets))
    if has_assets:
        bundle = POSTS_ROOT / slug
        return bundle / "index.md", bundle
    return POSTS_ROOT / f"{slug}.md", None


def counterpart_for(target: Path) -> Path:
    if target.name == "index.md":
        return POSTS_ROOT / f"{target.parent.name}.md"
    return POSTS_ROOT / target.stem / "index.md"


def assert_managed_if_exists(path: Path) -> None:
    if not path.exists():
        return
    parsed = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    if not parsed or parsed[0].get("managed_by") != MANAGED_BY:
        raise FileExistsError(f"refusing to overwrite unmanaged post: {path}")


def assert_target_is_managed(target: Path) -> None:
    assert_managed_if_exists(target)
    assert_managed_if_exists(counterpart_for(target))


def asset_tree_digest(root: Path) -> str | None:
    if not root.is_dir():
        return None
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files:
        return None

    h = hashlib.sha256()
    for path in files:
        h.update(path.relative_to(root).as_posix().encode("utf-8"))
        h.update(b"\0")
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                h.update(chunk)
    return h.hexdigest()


def assets_differ(source_assets: Path, bundle: Path | None) -> bool:
    source_digest = asset_tree_digest(source_assets)
    destination = bundle / "assets" if bundle is not None else None
    destination_digest = asset_tree_digest(destination) if destination is not None else None
    return source_digest != destination_digest


def remove_managed_counterpart(target: Path) -> None:
    counterpart = counterpart_for(target)
    if not counterpart.exists():
        return

    assert_managed_if_exists(counterpart)
    if counterpart.name == "index.md":
        shutil.rmtree(counterpart.parent)
    else:
        counterpart.unlink()


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

    validate_source_integrity(folder, body)

    source_assets = folder / "assets"
    digest = package_digest(meta_bytes, body_bytes, source_assets)
    fm = managed_frontmatter(slug=slug, meta=meta, digest=digest)
    output = "---\n" + dump_yaml(fm) + "---\n\n" + strip_leading_h1(body)

    target, bundle = target_for(slug, source_assets)
    assert_target_is_managed(target)

    prior = target.read_text(encoding="utf-8") if target.exists() else None
    content_changed = prior != output
    asset_changed = assets_differ(source_assets, bundle)
    counterpart_exists = counterpart_for(target).exists()
    changed = content_changed or asset_changed or counterpart_exists

    mode = "WRITE" if write else "DRY-RUN"
    reasons = []
    if content_changed:
        reasons.append("content")
    if asset_changed:
        reasons.append("assets")
    if counterpart_exists:
        reasons.append("layout")
    state = "changed:" + ",".join(reasons) if reasons else "unchanged"
    print(f"{mode} {slug}: {state} -> {target.relative_to(REPO_ROOT)}")

    if not write or not changed:
        return changed

    POSTS_ROOT.mkdir(parents=True, exist_ok=True)
    remove_managed_counterpart(target)

    if bundle is not None:
        bundle.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="utf-8")
        destination = bundle / "assets"
        if destination.exists():
            shutil.rmtree(destination)
        if source_assets.is_dir():
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
    parser = argparse.ArgumentParser(
        description="One-way publisher from ai-research-reports to Marginalia."
    )
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
