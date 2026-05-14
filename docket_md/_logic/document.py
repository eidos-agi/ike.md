"""Document CRUD: create, list, view, update."""

from __future__ import annotations

from ..config import resolve_project
from ..files import (
    document_path,
    find_document_file,
    list_documents,
    next_document_id,
    read_markdown,
    write_markdown,
)
from ._common import today


def document_create(
    project_id: str, title: str, content: str = "", tags: list[str] | None = None
) -> str:
    """Create a project document."""
    project_root = resolve_project(project_id)
    id = next_document_id(project_root)
    fm: dict = {"id": id, "title": title, "created": today()}
    if tags:
        fm["tags"] = tags
    write_markdown(document_path(project_root, id, title), fm, content)
    return f"Created document **{id}** — {title}"


def document_list(project_id: str) -> str:
    """List all documents."""
    project_root = resolve_project(project_id)
    docs = list_documents(project_root)
    if not docs:
        return "No documents."
    return "\n".join(
        f"**{d.frontmatter['id']}** — {d.frontmatter['title']}" for d in docs
    )


def document_view(project_id: str, document_id: str) -> str:
    """View a document by ID."""
    project_root = resolve_project(project_id)
    fp = find_document_file(project_root, document_id)
    if not fp:
        return f"Document {document_id} not found."
    doc = read_markdown(fp)
    return f"## {doc.frontmatter['id']} — {doc.frontmatter['title']}\n\n{doc.content}"


def document_update(
    project_id: str,
    document_id: str,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    append_content: str | None = None,
) -> str:
    """Update a document."""
    project_root = resolve_project(project_id)
    fp = find_document_file(project_root, document_id)
    if not fp:
        return f"Document {document_id} not found."
    doc = read_markdown(fp)
    fm = {**doc.frontmatter, "updated": today()}
    if title is not None:
        fm["title"] = title
    if tags is not None:
        fm["tags"] = tags
    if append_content:
        new_content = f"{doc.content}\n\n{append_content}".strip()
    elif content is not None:
        new_content = content
    else:
        new_content = doc.content
    write_markdown(fp, fm, new_content)
    return f"Updated **{fm['id']}** — {fm['title']}"
