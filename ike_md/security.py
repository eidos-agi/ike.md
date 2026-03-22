"""Path traversal prevention."""

import os


def safe_path(root: str, *parts: str) -> str:
    """Resolve a safe path within a root directory. Prevents path traversal."""
    resolved = os.path.normpath(os.path.join(os.path.abspath(root), *parts))
    if not resolved.startswith(os.path.abspath(root)):
        raise ValueError(f"Path traversal attempt: {'/'.join(parts)}")
    return resolved
