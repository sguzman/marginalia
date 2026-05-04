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
HUGO_STANDARD_YAML = DATA_DIR / "hugo-frontmatter-standard.yaml"

PERSONAL_SLUGS: set[str] = {
    "aggression-as-iteration-rate",
    "the-tragedy-of-formalism",
    "death-by-manager",
    "what-is-in-a-book",
    "what-is-an-inclusive-institution",
    "truth-as-process",
}

IGNORED_SLUGS: set[str] = {
    # Duplicate/erroneous import; keep `federal-legal-landscape` and `kern-county-cannabis-legal-environment` instead.
    "kern-weed",
    # Duplicate article; keep `american-judicial-process` as the canonical blog slug.
    "judges-in-the-judicial-process-of-the-united-states",
}


class FoldedStr(str):
    pass


def _represent_folded_str(dumper: yaml.Dumper, data: FoldedStr) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=">")


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:  # type: ignore[override]
        return super().increase_indent(flow, indentless=False)


IndentDumper.add_representer(FoldedStr, _represent_folded_str)


def die(message: str, *, code: int = 1) -> None:
    raise SystemExit(f"error: {message}")


def load_yaml_first_doc(path: Path) -> dict[str, Any]:
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    for doc in docs:
        if isinstance(doc, dict) and doc:
            return doc
    return {}


def dump_yaml(data: Any) -> str:
    return yaml.dump(
        data,
        Dumper=IndentDumper,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
        indent=2,
        default_flow_style=False,
    )


def sort_deep(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sort_deep(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [sort_deep(v) for v in value]
    return value


def load_hugo_standard() -> dict[str, Any]:
    if not HUGO_STANDARD_YAML.exists():
        die(f"missing hugo standard: {HUGO_STANDARD_YAML}")
    docs = list(yaml.safe_load_all(HUGO_STANDARD_YAML.read_text(encoding="utf-8")))
    for doc in docs:
        if isinstance(doc, dict) and doc:
            return doc
    die(f"unable to parse hugo standard: {HUGO_STANDARD_YAML}")


HUGO_STANDARD = load_hugo_standard()


def read_h1_from_text(text: str) -> str | None:
    for line in text.splitlines()[:20]:
        if line.startswith("# "):
            return line[2:].strip()
    return None


def norm_key(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


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
    s = s.replace("_", "")
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


def ensure_h1(md_text: str, title: str) -> str:
    lines = md_text.lstrip("\ufeff").splitlines()
    if not lines:
        return f"# {title}\n"

    if lines[0].startswith("# "):
        return md_text if md_text.endswith("\n") else md_text + "\n"

    out = f"# {title}\n\n" + md_text.lstrip("\n")
    return out if out.endswith("\n") else out + "\n"


def replace_first_h1(md_text: str, title: str) -> str:
    lines = md_text.lstrip("\ufeff").splitlines()
    if not lines:
        return f"# {title}\n"
    if not lines[0].startswith("# "):
        return ensure_h1(md_text, title)
    lines[0] = "# " + title
    out = "\n".join(lines)
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


def is_generic_title(title: str | None) -> bool:
    if not title:
        return True
    t = re.sub(r"\s+", " ", title).strip().lower()
    # Titles that are basically a slug are not acceptable as final titles.
    if "-" in t and " " not in t:
        return True
    if re.match(r"^\d+[a-z].*", t):
        return True
    return t in {
        "executive summary",
        "executative summary",
        "summary",
        "abstract",
        "introduction",
    }


def humanize_slug(slug: str) -> str:
    # Keep small tokens like v2/v3 as-is; title-case normal words.
    parts = [p for p in re.split(r"[-_]+", slug.strip()) if p]
    out: list[str] = []
    for p in parts:
        # Drop leading numeric prefixes like "1inventing" -> "inventing"
        p = re.sub(r"^\d+(?=[a-zA-Z])", "", p)
        if not p:
            continue
        if re.fullmatch(r"v\d+", p, flags=re.IGNORECASE):
            out.append(p.lower())
        elif p.lower() in {"us", "u", "s"}:
            out.append(p.upper())
        else:
            out.append(p[:1].upper() + p[1:])
    return " ".join(out) if out else "Untitled"


def title_from_source_docx(meta: dict[str, Any]) -> str | None:
    report = meta.get("report")
    if not isinstance(report, dict):
        return None
    conv = report.get("conversion")
    if not isinstance(conv, dict):
        return None
    src = conv.get("source_docx")
    if not isinstance(src, str) or not src.strip() or src.strip() == "(standalone-md)":
        return None
    stem = Path(src.strip()).stem
    # Docx names often contain punctuation; slugify-ish then humanize for a clean title.
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return humanize_slug(slug)


def prefer_h1_title(meta_title: str | None, h1_title: str | None, fallback: str) -> str:
    candidates = [h1_title, meta_title, fallback]
    for c in candidates:
        if not c:
            continue
        c = normalize_title(str(c).strip())
        if c and not is_generic_title(c):
            return c
    # If everything is generic, keep fallback but normalized.
    fb = normalize_title(fallback.strip() or "Untitled")
    return fb or "Untitled"


def assets_file_count(folder: Path) -> int:
    assets = folder / "assets"
    if not assets.exists():
        return 0
    return sum(1 for p in assets.rglob("*") if p.is_file())


def has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def clean_scalar_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return strip_markdown(value).strip()


def clean_summary_text(value: Any, *, max_len: int) -> str:
    text = clean_scalar_text(value)
    if not text:
        return ""
    return shorten(text, max_len=max_len)


def looks_bad_excerpt(text: str, *, title: str) -> bool:
    t = clean_scalar_text(text)
    if not t:
        return True
    if "http://" in t.lower() or "https://" in t.lower() or "(https:" in t.lower():
        return True
    if norm_key(t) == norm_key(title):
        return True
    if len(t) < 40:
        return True
    return False


def choose_best_excerpt(
    candidates: list[Any], *, title: str, max_len: int, allow_title_fallback: bool = True
) -> str:
    for candidate in candidates:
        text = clean_summary_text(candidate, max_len=max_len)
        if text and not looks_bad_excerpt(text, title=title):
            return text
    for candidate in candidates:
        text = clean_summary_text(candidate, max_len=max_len)
        if text:
            return text
    return clean_summary_text(title if allow_title_fallback else "", max_len=max_len)


def looks_bad_title(text: str) -> bool:
    t = clean_scalar_text(text)
    if not t:
        return True
    if "http://" in t.lower() or "https://" in t.lower() or "(https:" in t.lower():
        return True
    return False


def choose_best_title(candidates: list[Any], fallback: str) -> str:
    for candidate in candidates:
        text = clean_scalar_text(candidate)
        if text and not looks_bad_title(text):
            return text
    for candidate in candidates:
        text = clean_scalar_text(candidate)
        if text:
            return text
    return clean_scalar_text(fallback) or fallback


def as_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if re.fullmatch(r"-?\d+", raw):
            return int(raw)
    return default


def meaningful_cover(meta: dict[str, Any]) -> str:
    for key in ("cover-image", "cover_image"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def build_filtered_meta(
    *,
    meta_source: dict[str, Any],
    title: str,
    description: str,
    abstract: str,
    slug: str,
    date: str,
    categories: list[str],
    tags: list[str],
    keywords: list[str],
) -> dict[str, Any]:
    required = HUGO_STANDARD.get("meta_required", {})
    optional = HUGO_STANDARD.get("meta_optional", {})

    meta_out: dict[str, Any] = {}

    for key, default in required.items():
        if key == "title":
            meta_out[key] = title
        elif key == "subtitle":
            value = clean_scalar_text(meta_source.get(key))
            meta_out[key] = value
        elif key == "abstract":
            meta_out[key] = abstract
        elif key == "description":
            meta_out[key] = description
        elif key == "creator":
            creators = as_string_list(meta_source.get(key))
            if not creators:
                creators = ["Salvador Guzman"]
            meta_out[key] = creators
        elif key == "publisher":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key == "rights":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key == "license":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key == "lang":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key == "language":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key in {"subject", "subjects"}:
            values = as_string_list(meta_source.get(key))
            if key == "subjects" and not values:
                values = as_string_list(meta_source.get("subject"))
            meta_out[key] = values
        elif key == "reference-section-title":
            meta_out[key] = clean_scalar_text(meta_source.get(key))
        elif key in {"toc", "number-sections"}:
            value = meta_source.get(key)
            meta_out[key] = value if isinstance(value, bool) else bool(default)
        elif key == "toc-depth":
            value = meta_source.get(key)
            meta_out[key] = as_int(value, int(default))
        elif key == "toc-title":
            value = clean_scalar_text(meta_source.get(key)) or str(default)
            meta_out[key] = value
        elif key in {"revision", "edition", "format", "dataset_id", "identifier"}:
            if key == "identifier":
                value = clean_scalar_text(meta_source.get(key)) or slug
            elif key == "format":
                value = clean_scalar_text(meta_source.get(key)) or str(default)
            else:
                value = clean_scalar_text(meta_source.get(key))
            meta_out[key] = value
        elif key == "library_of_congress_classification":
            loc = meta_source.get(key)
            if not isinstance(loc, dict):
                loc = {}
            meta_out[key] = {
                "class": clean_scalar_text(loc.get("class")),
                "description": clean_scalar_text(loc.get("description")),
                "label": clean_scalar_text(loc.get("label")),
            }
        elif key == "report":
            report_src = meta_source.get("report")
            if not isinstance(report_src, dict):
                report_src = {}
            report_required = default if isinstance(default, dict) else {}
            report_out: dict[str, Any] = {}
            for rkey, rdefault in report_required.items():
                if rkey == "conversion":
                    conv_src = report_src.get("conversion")
                    if not isinstance(conv_src, dict):
                        conv_src = {}
                    conv_default = rdefault if isinstance(rdefault, dict) else {}
                    report_out[rkey] = {
                        "date": clean_scalar_text(conv_src.get("date")) or clean_scalar_text(conv_default.get("date")),
                        "source_docx": clean_scalar_text(conv_src.get("source_docx")) or clean_scalar_text(conv_default.get("source_docx")),
                        "tool": clean_scalar_text(conv_src.get("tool")) or clean_scalar_text(conv_default.get("tool")),
                    }
                elif isinstance(rdefault, list):
                    report_out[rkey] = as_string_list(report_src.get(rkey))
                elif isinstance(rdefault, bool):
                    value = report_src.get(rkey)
                    report_out[rkey] = value if isinstance(value, bool) else bool(rdefault)
                elif isinstance(rdefault, int):
                    value = report_src.get(rkey)
                    report_out[rkey] = as_int(value, int(rdefault))
                else:
                    report_out[rkey] = clean_scalar_text(report_src.get(rkey))
            meta_out[key] = report_out
        else:
            meta_out[key] = meta_source.get(key, default)

    for key in optional:
        if key in {"slug", "date", "type", "status"}:
            value = {
                "slug": slug,
                "date": date,
                "type": clean_scalar_text(meta_source.get("type")) or "article",
                "status": clean_scalar_text(meta_source.get("status")) or "published",
            }[key]
            if has_meaningful_value(value):
                meta_out[key] = value
        elif key in {"categories", "tags", "keywords"}:
            value = {
                "categories": categories,
                "tags": tags,
                "keywords": keywords,
            }[key]
            if has_meaningful_value(value):
                meta_out[key] = value
        elif key == "number-sections":
            value = meta_source.get(key)
            if isinstance(value, bool):
                meta_out[key] = value
        elif key == "plate_id":
            value = clean_scalar_text(meta_source.get(key))
            if has_meaningful_value(value):
                meta_out[key] = value
        elif key in {"cover-image", "cover_image"}:
            cover = meaningful_cover(meta_source)
            if cover:
                meta_out["cover-image"] = cover
                meta_out["cover_image"] = cover
        elif key in {"epub-cover-image", "epub_cover_image"}:
            value = clean_scalar_text(meta_source.get(key))
            if not value:
                value = meaningful_cover(meta_source)
            if value:
                meta_out["epub-cover-image"] = value
                meta_out["epub_cover_image"] = value
        elif key == "epub-title-page":
            value = meta_source.get(key)
            if isinstance(value, bool):
                meta_out[key] = value
        elif key == "epub-chapter-level":
            value = meta_source.get(key)
            if isinstance(value, int) or (isinstance(value, str) and value.strip()):
                meta_out[key] = as_int(value, 2)

    return sort_deep(meta_out)


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
        meta_title = str(self.meta.get("title")) if self.meta.get("title") else None
        h1 = self.h1
        fallback = humanize_slug(self.slug)
        # If docx conversion exists, prefer its filename stem over generic titles.
        src_title = title_from_source_docx(self.meta)
        if src_title and not is_generic_title(src_title):
            # Only use this if both meta+h1 are generic or empty.
            if is_generic_title(meta_title) and is_generic_title(h1):
                return strip_markdown(src_title).strip() or src_title
        t = prefer_h1_title(meta_title, h1, fallback)
        t = strip_markdown(t).strip()
        return t or fallback

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


AI_OUTRO_PAT = re.compile(
    r"(?im)^(#+\s*(next steps|follow[- ]?ups?)\s*$|"
    r".*\b(do you want me to|would you like me to|want me to|"
    r"i can (also )?(generate|write|draft|help)|"
    r"generate more (articles|posts)|"
    r"let me know if you(?:'d| would) like)\b.*)$"
)


NEXT_STEPS_HEADING_PAT = re.compile(
    r"(?im)^(#+)\s*(\d+[\.\)]\s*)?(next[- ]step|next steps)\b.*$|\*\*next[- ]step.*\*\*\s*$"
)


def remove_next_steps_section(body: str) -> str:
    """
    Remove a 'Next steps' / 'Next-step research plan' section that is meant as
    assistant-to-user guidance, while preserving trailing references/bibliography.
    """
    lines = body.splitlines()
    if not lines:
        return body

    heading_pat = re.compile(r"(?im)^(#+)\s+")
    refs_pat = re.compile(r"(?im)^#+\s*(references|bibliography)\b")

    i = 0
    out_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        m = NEXT_STEPS_HEADING_PAT.match(line.strip())

        # Heading-based section removal.
        if m and line.lstrip().startswith("#"):
            level = len(m.group(1))
            i += 1
            while i < len(lines):
                if refs_pat.match(lines[i].strip()):
                    break
                hm = heading_pat.match(lines[i].strip())
                if hm:
                    next_level = len(hm.group(1))
                    if next_level <= level:
                        break
                i += 1
            continue

        # Bold-only "Next-Step..." removal: drop until blank line.
        if m and line.strip().startswith("**"):
            i += 1
            while i < len(lines) and lines[i].strip():
                i += 1
            continue

        out_lines.append(line)
        i += 1

    return "\n".join(out_lines).rstrip() + "\n"


INLINE_NEXT_STEPS_PAT = re.compile(r"(?i)\bnext[- ]step research plan\b|\bnext steps\b")


def remove_inline_next_steps_blocks(body: str) -> str:
    """
    Remove inline 'Next steps' prompts embedded inside paragraphs, typically followed by a dash list.
    Conservative: only triggers when the line itself mentions next steps and the following lines are list items.
    """
    lines = body.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r"(?i)\bnext[- ]step research plan\s*:", line):
            # Drop everything from the marker to end of line.
            cut = re.search(r"(?i)\bnext[- ]step research plan\s*:", line)
            assert cut
            line = line[: cut.start()].rstrip()
            if line:
                out.append(line)
            i += 1
            continue
        if re.match(r"(?i)^\s*by pursuing these next steps\b", line.strip()):
            i += 1
            continue
        if (
            INLINE_NEXT_STEPS_PAT.search(line)
            and i + 1 < len(lines)
            and lines[i + 1].lstrip().startswith("-")
        ):
            i += 1
            while i < len(lines) and (
                lines[i].lstrip().startswith("-") or not lines[i].strip()
            ):
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out).rstrip() + "\n"


def trim_ai_outro(body: str) -> str:
    lines = body.splitlines()
    if not lines:
        return body
    # Only trim if the trigger appears near the end (prevents accidental mid-article deletes).
    window_start = max(0, len(lines) - 80)
    tail = "\n".join(lines[window_start:])
    m = None
    for match in AI_OUTRO_PAT.finditer(tail):
        m = match
    if not m:
        return body
    # Find the absolute line index of the first matched line.
    match_line = tail[: m.start()].count("\n")
    cut_at = window_start + match_line
    # Trim and drop trailing blank lines.
    out = "\n".join(lines[:cut_at]).rstrip() + "\n"
    return out


def collect_articles() -> list[Article]:
    if not MD_ROOT.exists():
        die(f"missing md root: {MD_ROOT}")

    articles: list[Article] = []
    for folder in sorted([p for p in MD_ROOT.iterdir() if p.is_dir()]):
        if folder.name in IGNORED_SLUGS:
            continue
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


def fix_article_main_md(a: Article) -> bool:
    md_text = a.md_path.read_text(encoding="utf-8")
    h1 = read_h1_from_text(md_text)
    desired = a.title
    if h1 and not is_generic_title(h1):
        return False
    if not desired or is_generic_title(desired):
        return False
    new_text = replace_first_h1(md_text, desired)
    if new_text == md_text:
        return False
    a.md_path.write_text(new_text, encoding="utf-8")
    return True


def build_standard_frontmatter(
    *,
    slug: str,
    title: str,
    date: str,
    description: str,
    summary: str,
    meta_source: dict[str, Any],
    lastmod: str,
    is_personal: bool,
    paragraph_fallback: str = "",
) -> dict[str, Any]:
    report_src = meta_source.get("report") if isinstance(meta_source.get("report"), dict) else {}
    clean_title = choose_best_title(
        [
            title,
            meta_source.get("linkTitle"),
            meta_source.get("title"),
            report_src.get("name") if isinstance(report_src, dict) else "",
            report_src.get("topic") if isinstance(report_src, dict) else "",
        ],
        fallback=title or slug,
    )
    description = choose_best_excerpt(
        [
            description,
            meta_source.get("description"),
            meta_source.get("summary"),
            meta_source.get("abstract"),
            paragraph_fallback,
        ],
        title=clean_title,
        max_len=240,
    ) or clean_title
    summary = choose_best_excerpt(
        [
            summary,
            meta_source.get("abstract"),
            meta_source.get("summary"),
            meta_source.get("description"),
            paragraph_fallback,
        ],
        title=clean_title,
        max_len=800,
    ) or description

    categories = as_string_list(meta_source.get("categories"))
    tags = as_string_list(meta_source.get("tags"))
    keywords = as_string_list(meta_source.get("keywords"))

    meta_filtered = build_filtered_meta(
        meta_source=meta_source,
        title=clean_title,
        description=description,
        abstract=summary,
        slug=slug,
        date=date,
        categories=categories,
        tags=tags,
        keywords=keywords,
    )

    authors_list = ["Salvador Guzman"] + ([] if is_personal else ["ChatGPT"])

    frontmatter: dict[str, Any] = {
        "ai_generated": (not is_personal),
        "authors": authors_list,
        "categories": categories,
        "date": date,
        "description": FoldedStr(description),
        "draft": False,
        "keywords": keywords,
        "lastmod": lastmod,
        "layout": "single",
        "linkTitle": clean_title if len(clean_title) <= 60 else clean_title[:57].rstrip() + "…",
        "markup": "goldmark",
        "meta": meta_filtered,
        "outputs": ["HTML", "RSS"],
        "slug": slug,
        "summary": FoldedStr(summary),
        "tags": tags,
        "title": clean_title,
    }

    aliases = meta_source.get("aliases")
    if isinstance(aliases, list):
        clean_aliases = [str(a).strip() for a in aliases if str(a).strip()]
        if clean_aliases:
            frontmatter["aliases"] = clean_aliases

    expiry = clean_scalar_text(meta_source.get("expiryDate"))
    if expiry:
        frontmatter["expiryDate"] = expiry

    url = clean_scalar_text(meta_source.get("url"))
    if url:
        frontmatter["url"] = url

    weight = meta_source.get("weight")
    if isinstance(weight, int) and weight != 0:
        frontmatter["weight"] = weight

    return sort_deep(frontmatter)


def hugo_frontmatter_from_article(a: Article) -> dict[str, Any]:
    meta_source = dict(a.meta)
    summary = str(meta_source.get("summary") or meta_source.get("abstract") or a.abstract)
    return build_standard_frontmatter(
        slug=a.slug,
        title=a.title,
        date=a.date,
        description=str(meta_source.get("description") or a.description),
        summary=summary,
        meta_source=meta_source,
        lastmod=dt.date.today().isoformat(),
        is_personal=(a.slug in PERSONAL_SLUGS),
        paragraph_fallback=first_paragraph(a.md_text) or "",
    )


def write_post(a: Article, *, dry_run: bool) -> tuple[Path, bool]:
    fm = hugo_frontmatter_from_article(a)
    body = strip_leading_h1(a.md_text)
    body = remove_next_steps_section(body)
    body = remove_inline_next_steps_blocks(body)
    body = trim_ai_outro(body)

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

    # Never overwrite personal posts with generated content.
    if a.slug in PERSONAL_SLUGS:
        return target_md, False

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


def iter_post_paths() -> list[Path]:
    out: list[Path] = []
    if not POSTS_DIR.exists():
        return out
    out.extend(sorted(POSTS_DIR.glob("*.md")))
    for d in sorted([p for p in POSTS_DIR.iterdir() if p.is_dir()]):
        idx = d / "index.md"
        if idx.exists():
            out.append(idx)
    return out


def load_post_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = split_hugo_frontmatter(text)
    if not parts:
        return None
    try:
        data = yaml.safe_load(parts[0])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def post_frontmatter_valid_yaml(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = split_hugo_frontmatter(text)
    if not parts:
        return False
    try:
        data = yaml.safe_load(parts[0])
        if not isinstance(data, dict):
            return False
        # Treat clearly broken frontmatter as invalid (e.g. meta parsed as null).
        if "meta" in data and data.get("meta") is None:
            return False
        return True
    except Exception:
        return False


def split_hugo_frontmatter(text: str) -> tuple[str, str] | None:
    """
    Robustly split Hugo frontmatter from content.
    Requires frontmatter delimited by standalone lines: ---.
    Returns (frontmatter_yaml_text, body_text_including_leading_newline_if_any).
    """
    if not text.startswith("---\n"):
        return None
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        return None
    fm = text[4:end]
    body = text[end + len(marker) :]
    return fm, body


def post_slug_from_path(path: Path, fm: dict[str, Any]) -> str:
    slug = fm.get("slug")
    if isinstance(slug, str) and slug.strip():
        return slug.strip()
    if path.name == "index.md":
        return path.parent.name
    return path.stem


def remove_post(path: Path) -> None:
    # If it's a bundle index, remove the whole bundle folder; otherwise remove the leaf.
    if path.name == "index.md":
        folder = path.parent
        for p in sorted(folder.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        folder.rmdir()
    else:
        path.unlink()


def dedupe_posts(*, preferred_slugs: set[str], dry_run: bool) -> tuple[int, int]:
    """
    Remove duplicates by slug and by (title,date). Prefer keeping anything whose slug is in preferred_slugs.
    Returns (removed_by_slug, removed_by_title_date).
    """
    paths = iter_post_paths()
    records: list[tuple[Path, dict[str, Any]]] = []
    for p in paths:
        fm = load_post_frontmatter(p)
        if fm:
            records.append((p, fm))

    # 1) Dedupe by slug.
    by_slug: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for p, fm in records:
        slug = post_slug_from_path(p, fm)
        by_slug.setdefault(slug, []).append((p, fm))

    removed_slug = 0
    for slug, group in by_slug.items():
        if len(group) <= 1:
            continue
        # Keep preferred slug path if possible, else keep shortest path string (stable).
        keep = None
        if slug in preferred_slugs:
            # If multiple, prefer bundle index (assets) over leaf.
            bundle = [g for g in group if g[0].name == "index.md"]
            keep = (bundle[0] if bundle else group[0])
        else:
            keep = sorted(group, key=lambda x: str(x[0]))[0]
        for p, _ in group:
            if p == keep[0]:
                continue
            if not dry_run:
                remove_post(p)
            removed_slug += 1

    # Refresh after deletions.
    paths = iter_post_paths()
    records = []
    for p in paths:
        fm = load_post_frontmatter(p)
        if fm:
            records.append((p, fm))

    # 2) Dedupe by (title, date).
    by_key: dict[tuple[str, str], list[tuple[Path, dict[str, Any]]]] = {}
    for p, fm in records:
        title = fm.get("title")
        date = fm.get("date")
        if not isinstance(title, str) or not title.strip():
            continue
        key = (norm_key(title), str(date or "").strip())
        by_key.setdefault(key, []).append((p, fm))

    removed_td = 0
    for key, group in by_key.items():
        if len(group) <= 1:
            continue
        # Prefer keeping a post whose slug is a preferred slug.
        def score(item: tuple[Path, dict[str, Any]]) -> tuple[int, int, str]:
            p, fm = item
            slug = post_slug_from_path(p, fm)
            prefer = 1 if slug in preferred_slugs else 0
            is_bundle = 1 if p.name == "index.md" else 0
            return (prefer, is_bundle, str(p))

        keep = sorted(group, key=score, reverse=True)[0]
        for p, _ in group:
            if p == keep[0]:
                continue
            if not dry_run:
                remove_post(p)
            removed_td += 1

    return removed_slug, removed_td


def dedupe_posts_by_title_only(*, preferred_slugs: set[str], dry_run: bool) -> int:
    """
    Remove duplicates that share the same normalized title, regardless of date.
    Intended to catch a few lingering duplicates where dates differ.
    Prefer keeping preferred_slugs; otherwise keep the oldest date (stable).
    """
    paths = iter_post_paths()
    records: list[tuple[Path, dict[str, Any]]] = []
    for p in paths:
        fm = load_post_frontmatter(p)
        if fm:
            records.append((p, fm))

    def norm_title_only(s: str) -> str:
        s = strip_markdown(s).lower()
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    by_title: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for p, fm in records:
        title = fm.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        by_title.setdefault(norm_title_only(title), []).append((p, fm))

    removed = 0
    for _, group in by_title.items():
        if len(group) <= 1:
            continue

        def score(item: tuple[Path, dict[str, Any]]) -> tuple[int, str, int, str]:
            p, fm = item
            slug = post_slug_from_path(p, fm)
            prefer = 1 if slug in preferred_slugs else 0
            date = str(fm.get("date") or "")
            # older first
            return (prefer, date, 1 if p.name == "index.md" else 0, str(p))

        keep = sorted(group, key=score, reverse=True)[0]
        for p, _ in group:
            if p == keep[0]:
                continue
            # Never delete preferred slugs in this phase.
            fm = load_post_frontmatter(p) or {}
            slug = post_slug_from_path(p, fm) if fm else (p.parent.name if p.name == "index.md" else p.stem)
            if slug in preferred_slugs:
                continue
            if not dry_run:
                remove_post(p)
            removed += 1

    return removed


def repair_invalid_posts(*, article_by_slug: dict[str, Article], dry_run: bool) -> int:
    """
    If a post has invalid YAML frontmatter, overwrite it from tmp source when available.
    """
    repaired = 0
    for path in iter_post_paths():
        if post_frontmatter_valid_yaml(path):
            continue
        # Best-effort slug from path.
        slug = path.parent.name if path.name == "index.md" else path.stem
        a = article_by_slug.get(slug)
        if not a:
            continue
        repaired += 1
        if not dry_run:
            # Ensure we replace the broken file entirely.
            if path.exists():
                remove_post(path) if path.name == "index.md" else path.unlink()
            write_post(a, dry_run=False)
    return repaired


def fix_posts_authorship(*, dry_run: bool) -> int:
    """
    Enforce authorship policy across *all* posts under content/posts:
    - personal slugs: authors=[Salvador Guzman], ai_generated=false
    - everything else: authors=[Salvador Guzman, ChatGPT], ai_generated=true
    Returns number of changed posts.
    """
    changed = 0
    for path in iter_post_paths():
        text = path.read_text(encoding="utf-8", errors="replace")
        parts = split_hugo_frontmatter(text)
        if not parts:
            continue
        fm_txt, body = parts
        try:
            fm = yaml.safe_load(fm_txt) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue

        slug = post_slug_from_path(path, fm)
        is_personal = slug in PERSONAL_SLUGS
        desired_authors = ["Salvador Guzman"] + ([] if is_personal else ["ChatGPT"])

        authors = fm.get("authors")
        if isinstance(authors, str):
            current = [authors]
        elif isinstance(authors, list):
            current = [str(a) for a in authors]
        else:
            current = []

        new_fm = dict(fm)
        if current != desired_authors:
            new_fm["authors"] = desired_authors
        new_fm["ai_generated"] = (not is_personal)

        if new_fm != fm:
            changed += 1
            if not dry_run:
                out = "---\n" + dump_yaml(new_fm) + "---\n" + body
                path.write_text(out, encoding="utf-8")

    return changed


def ensure_rich_meta_for_post(frontmatter: dict[str, Any], body: str) -> dict[str, Any]:
    fm = dict(frontmatter)
    meta_in = fm.get("meta")
    meta_source = dict(meta_in) if isinstance(meta_in, dict) else {}

    slug = fm.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        slug = ""
    slug = slug.strip()

    title = clean_scalar_text(fm.get("title"))
    if not title:
        title = clean_scalar_text(meta_source.get("title")) or humanize_slug(slug or "untitled")

    desc = clean_scalar_text(fm.get("description"))
    if not desc:
        desc = clean_scalar_text(meta_source.get("description")) or clean_summary_text(first_paragraph(body) or title, max_len=240)

    summary = clean_scalar_text(fm.get("summary"))
    if not summary:
        summary = clean_scalar_text(meta_source.get("abstract")) or clean_scalar_text(meta_source.get("summary"))
    if not summary:
        summary = clean_summary_text(first_paragraph(body) or desc or title, max_len=800)

    date = clean_scalar_text(fm.get("date")) or clean_scalar_text(meta_source.get("date")) or dt.date.today().isoformat()
    lastmod = clean_scalar_text(fm.get("lastmod")) or clean_scalar_text(meta_source.get("lastmod")) or dt.date.today().isoformat()
    is_personal = slug in PERSONAL_SLUGS

    # Let existing post metadata fill source gaps for posts not regenerated from tmp.
    for key in ("categories", "tags", "keywords", "aliases", "url", "expiryDate", "weight"):
        if key not in meta_source and key in fm:
            meta_source[key] = fm.get(key)
    for key in (
        "title",
        "subtitle",
        "description",
        "abstract",
        "summary",
        "identifier",
        "dataset_id",
        "lang",
        "language",
        "license",
        "publisher",
        "rights",
        "reference-section-title",
        "revision",
        "edition",
        "format",
        "library_of_congress_classification",
        "report",
        "subject",
        "subjects",
        "creator",
        "toc",
        "toc-depth",
        "toc-title",
        "number-sections",
        "status",
        "type",
        "cover-image",
        "cover_image",
        "epub-cover-image",
        "epub_cover_image",
        "epub-title-page",
        "epub-chapter-level",
        "slug",
        "date",
        "plate_id",
    ):
        if key not in meta_source and key in fm:
            meta_source[key] = fm.get(key)

    return build_standard_frontmatter(
        slug=slug,
        title=title,
        date=date,
        description=desc,
        summary=summary,
        meta_source=meta_source,
        lastmod=lastmod,
        is_personal=is_personal,
        paragraph_fallback=first_paragraph(body) or "",
    )


def fix_posts_content_and_metadata(*, dry_run: bool) -> int:
    changed = 0
    for path in iter_post_paths():
        text = path.read_text(encoding="utf-8", errors="replace")
        parts = split_hugo_frontmatter(text)
        if not parts:
            continue
        fm_txt, body = parts
        try:
            fm = yaml.safe_load(fm_txt) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue

        # Trim AI outro from body and normalize title markdown.
        new_body = body
        # body starts with newline; keep it
        trimmed = body.lstrip("\n")
        trimmed = remove_next_steps_section(trimmed)
        trimmed = remove_inline_next_steps_blocks(trimmed)
        trimmed = trim_ai_outro(trimmed)
        new_body = "\n\n" + trimmed if trimmed else "\n"

        # Ensure slug exists for consistent metadata.
        slug = post_slug_from_path(path, fm)
        if not isinstance(fm.get("slug"), str) or not str(fm.get("slug")).strip():
            fm = dict(fm)
            fm["slug"] = slug

        new_fm = ensure_rich_meta_for_post(fm, trimmed)

        if new_fm != fm or new_body != body:
            changed += 1
            if not dry_run:
                out = "---\n" + dump_yaml(new_fm) + "---" + new_body
                path.write_text(out, encoding="utf-8")
    return changed


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
    fixed_md = 0
    for a in articles:
        fixed_meta += 1 if fix_article_yaml(a) else 0
        fixed_md += 1 if fix_article_main_md(a) else 0

    articles = collect_articles()  # reload after fixes
    wrote_articles = write_articles_yaml(articles, dry_run=args.dry_run)

    wrote_posts = 0
    if not args.no_publish:
        article_by_slug = {a.slug: a for a in articles}
        for a in articles:
            _, changed = write_post(a, dry_run=args.dry_run)
            wrote_posts += 1 if changed else 0

        # Remove accidental duplicates created by older/manual slugs.
        preferred = {a.slug for a in articles}
        removed_by_slug, removed_by_title_date = dedupe_posts(
            preferred_slugs=preferred, dry_run=args.dry_run
        )
        removed_by_title_only = dedupe_posts_by_title_only(
            preferred_slugs=preferred, dry_run=args.dry_run
        )
        fixed_authorship_posts = fix_posts_authorship(dry_run=args.dry_run)
        fixed_posts_cleanup = fix_posts_content_and_metadata(dry_run=args.dry_run)
        repaired_invalid_posts = repair_invalid_posts(
            article_by_slug=article_by_slug, dry_run=args.dry_run
        )
    else:
        removed_by_slug, removed_by_title_date = (0, 0)
        fixed_authorship_posts = 0
        fixed_posts_cleanup = 0
        repaired_invalid_posts = 0
        removed_by_title_only = 0

    print(
        "\n".join(
            [
                f"articles={len(articles)}",
                f"fixed_article_yaml={fixed_meta}",
                f"fixed_main_md_titles={fixed_md}",
                f"wrote_articles_yaml={int(wrote_articles)}",
                f"wrote_posts={wrote_posts}",
                f"removed_dupe_posts_by_slug={removed_by_slug}",
                f"removed_dupe_posts_by_title_date={removed_by_title_date}",
                f"removed_dupe_posts_by_title_only={removed_by_title_only}",
                f"fixed_posts_authorship={fixed_authorship_posts}",
                f"fixed_posts_cleanup={fixed_posts_cleanup}",
                f"repaired_invalid_posts={repaired_invalid_posts}",
            ]
        )
    )


if __name__ == "__main__":
    main()
