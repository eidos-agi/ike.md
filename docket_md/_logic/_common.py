"""Shared helpers — date + frontmatter formatters."""

from __future__ import annotations

from datetime import date


def today() -> str:
    return date.today().isoformat()


def format_task(fm: dict, content: str) -> str:
    lines = [
        f"## {fm['id']} — {fm['title']}",
        f"**Status:** {fm['status']}",
    ]
    if fm.get("priority"):
        lines.append(f"**Priority:** {fm['priority']}")
    if fm.get("milestone"):
        lines.append(f"**Milestone:** {fm['milestone']}")
    if fm.get("assignees"):
        lines.append(f"**Assignees:** {', '.join(fm['assignees'])}")
    if fm.get("tags"):
        lines.append(f"**Tags:** {', '.join(fm['tags'])}")
    if fm.get("dependencies"):
        lines.append(f"**Depends on:** {', '.join(fm['dependencies'])}")
    if fm.get("blocked_reason"):
        lines.append(f"**⛔ Blocked:** {fm['blocked_reason']}")
    lines.append(f"**Created:** {fm['created']}")
    if fm.get("updated"):
        lines.append(f"**Updated:** {fm['updated']}")

    if fm.get("acceptance-criteria"):
        lines.append("\n**Acceptance Criteria:**")
        for c in fm["acceptance-criteria"]:
            lines.append(f"- [ ] {c}")

    if fm.get("definition-of-done"):
        lines.append("\n**Definition of Done:**")
        for d in fm["definition-of-done"]:
            lines.append(f"- [ ] {d}")

    if content:
        lines.append("\n**Notes:**")
        lines.append(content)

    return "\n".join(lines)


def format_plan(fm: dict, content: str) -> str:
    lines = [
        f"## {fm['id']} — {fm['title']}",
        f"**Status:** {fm['status']}",
    ]
    if fm.get("milestone"):
        lines.append(f"**Milestone:** {fm['milestone']}")
    if fm.get("tags"):
        lines.append(f"**Tags:** {', '.join(fm['tags'])}")
    lines.append(f"**Created:** {fm['created']}")
    if fm.get("approved"):
        lines.append(f"**Approved:** {fm['approved']}")
    if fm.get("updated"):
        lines.append(f"**Updated:** {fm['updated']}")
    if fm.get("session_id"):
        lines.append(f"**Session:** {fm['session_id']}")

    if fm.get("verification"):
        lines.append("\n**Verification Checklist:**")
        for v in fm["verification"]:
            lines.append(f"- [ ] {v}")

    if content:
        lines.append("\n**Content:**")
        lines.append(content)

    return "\n".join(lines)
