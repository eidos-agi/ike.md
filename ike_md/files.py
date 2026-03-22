"""Markdown file I/O, ID generation, task/milestone/document operations."""

import os
import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from .config import IKE_DIR, DIRECTORIES
from .security import safe_path


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass
class ParsedFile:
    frontmatter: dict[str, Any]
    content: str
    file_path: str


# ── YAML formatting to match gray-matter ──────────────────────────────────────

class _GrayMatterDumper(yaml.SafeDumper):
    """Custom YAML dumper that matches gray-matter (js-yaml) output.

    Key differences from default PyYAML:
    - Strings that look like dates get single-quoted: '2026-03-22'
    - List items are indented 2 spaces under their key (default_flow_style=False
      + best_width handling doesn't do this, we need indent+offset config)
    """
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    # Quote strings that look like dates (YYYY-MM-DD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_GrayMatterDumper.add_representer(str, _str_representer)


# ── Read / Write ──────────────────────────────────────────────────────────────

def read_markdown(file_path: str) -> ParsedFile:
    with open(file_path) as f:
        raw = f.read()

    # Parse YAML frontmatter
    if raw.startswith("---\n"):
        end = raw.index("\n---\n", 4)
        fm_str = raw[4:end]
        content = raw[end + 5:].strip()
        frontmatter = yaml.safe_load(fm_str) or {}
        # Convert date objects back to strings (yaml.safe_load parses dates)
        for k, v in frontmatter.items():
            if hasattr(v, "isoformat"):
                frontmatter[k] = v.isoformat()
    else:
        frontmatter = {}
        content = raw.strip()

    return ParsedFile(frontmatter=frontmatter, content=content, file_path=file_path)


def write_markdown(file_path: str, frontmatter: dict[str, Any], content: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Filter out None values
    fm = {k: v for k, v in frontmatter.items() if v is not None}

    fm_str = yaml.dump(
        fm, Dumper=_GrayMatterDumper,
        default_flow_style=False, sort_keys=False, allow_unicode=True,
        indent=2,  # base indent
    )
    # gray-matter (js-yaml) indents list items under their key with 2 spaces.
    # PyYAML puts them at the same level. Fix by adding 2-space indent to list items
    # that follow a key line.
    lines = fm_str.split("\n")
    fixed = []
    in_list = False
    for line in lines:
        if line.startswith("- "):
            # This is a list item at root level — indent it
            fixed.append("  " + line)
            in_list = True
        else:
            in_list = False
            fixed.append(line)
    fm_str = "\n".join(fixed)

    with open(file_path, "w") as f:
        f.write("---\n")
        f.write(fm_str)
        f.write("---\n")
        if content:
            f.write(content)
            if not content.endswith("\n"):
                f.write("\n")
        else:
            f.write("\n")


# ── ID generation ─────────────────────────────────────────────────────────────

def _next_id(prefix: str, existing: list[str]) -> str:
    max_n = 0
    pattern = re.compile(rf"^{prefix}-(\d+)$", re.IGNORECASE)
    for id_str in existing:
        m = pattern.match(id_str)
        if m:
            n = int(m.group(1))
            max_n = max(max_n, n)
    return f"{prefix}-{str(max_n + 1).zfill(4)}"


def _slugify(title: str, max_len: int = 50) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    slug = slug.strip("-")
    return slug[:max_len]


# ── Tasks ─────────────────────────────────────────────────────────────────────

def _task_dir(project_root: str, completed: bool = False) -> str:
    subdir = DIRECTORIES["COMPLETED"] if completed else DIRECTORIES["TASKS"]
    return safe_path(project_root, IKE_DIR, subdir)


def list_tasks(project_root: str, include_completed: bool = False) -> list[ParsedFile]:
    results = []
    dirs = [_task_dir(project_root)]
    if include_completed:
        dirs.append(_task_dir(project_root, completed=True))

    for d in dirs:
        if not os.path.exists(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".md"):
                try:
                    results.append(read_markdown(os.path.join(d, f)))
                except Exception:
                    pass
    return results


def list_all_tasks(project_root: str) -> list[ParsedFile]:
    results = list_tasks(project_root, include_completed=True)
    archive_dir = safe_path(project_root, IKE_DIR, DIRECTORIES["ARCHIVE"])
    if os.path.exists(archive_dir):
        for f in sorted(os.listdir(archive_dir)):
            if f.endswith(".md"):
                try:
                    results.append(read_markdown(os.path.join(archive_dir, f)))
                except Exception:
                    pass
    return results


def next_task_id(project_root: str) -> str:
    existing = [t.frontmatter["id"] for t in list_tasks(project_root, include_completed=True)]
    # Also check archive
    archive_dir = safe_path(project_root, IKE_DIR, DIRECTORIES["ARCHIVE"])
    if os.path.exists(archive_dir):
        for f in sorted(os.listdir(archive_dir)):
            if f.endswith(".md"):
                try:
                    parsed = read_markdown(os.path.join(archive_dir, f))
                    existing.append(parsed.frontmatter["id"])
                except Exception:
                    pass
    return _next_id("TASK", existing)


def task_path(project_root: str, id: str, title: str, completed: bool = False) -> str:
    slug = _slugify(title)
    subdir = DIRECTORIES["COMPLETED"] if completed else DIRECTORIES["TASKS"]
    return safe_path(project_root, IKE_DIR, subdir, f"{id} - {slug}.md")


def find_task_file(project_root: str, id: str) -> str | None:
    dirs = [
        safe_path(project_root, IKE_DIR, DIRECTORIES["TASKS"]),
        safe_path(project_root, IKE_DIR, DIRECTORIES["COMPLETED"]),
        safe_path(project_root, IKE_DIR, DIRECTORIES["ARCHIVE"]),
    ]
    for d in dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.startswith(id):
                return os.path.join(d, f)
    return None


# ── Milestones ────────────────────────────────────────────────────────────────

def _milestone_dir(project_root: str) -> str:
    return safe_path(project_root, IKE_DIR, DIRECTORIES["MILESTONES"])


def list_milestones(project_root: str) -> list[ParsedFile]:
    d = _milestone_dir(project_root)
    if not os.path.exists(d):
        return []
    return [
        read_markdown(os.path.join(d, f))
        for f in sorted(os.listdir(d))
        if f.endswith(".md")
    ]


def next_milestone_id(project_root: str) -> str:
    existing = [m.frontmatter["id"] for m in list_milestones(project_root)]
    return _next_id("MS", existing)


def milestone_path(project_root: str, id: str, title: str) -> str:
    slug = _slugify(title)
    return safe_path(project_root, IKE_DIR, DIRECTORIES["MILESTONES"], f"{id} - {slug}.md")


def find_milestone_file(project_root: str, id: str) -> str | None:
    d = _milestone_dir(project_root)
    if not os.path.exists(d):
        return None
    for f in os.listdir(d):
        if f.startswith(id):
            return os.path.join(d, f)
    return None


# ── Documents ─────────────────────────────────────────────────────────────────

def _document_dir(project_root: str) -> str:
    return safe_path(project_root, IKE_DIR, DIRECTORIES["DOCUMENTS"])


def list_documents(project_root: str) -> list[ParsedFile]:
    d = _document_dir(project_root)
    if not os.path.exists(d):
        return []
    return [
        read_markdown(os.path.join(d, f))
        for f in sorted(os.listdir(d))
        if f.endswith(".md")
    ]


def next_document_id(project_root: str) -> str:
    existing = [d.frontmatter["id"] for d in list_documents(project_root)]
    return _next_id("DOC", existing)


def document_path(project_root: str, id: str, title: str) -> str:
    slug = _slugify(title)
    return safe_path(project_root, IKE_DIR, DIRECTORIES["DOCUMENTS"], f"{id} - {slug}.md")


def find_document_file(project_root: str, id: str) -> str | None:
    d = _document_dir(project_root)
    if not os.path.exists(d):
        return None
    for f in os.listdir(d):
        if f.startswith(id):
            return os.path.join(d, f)
    return None
