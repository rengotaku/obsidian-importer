"""File ID generation for obsidian-etl.

Generates SHA-256 based hash IDs for file tracking.
Migrated from src/etl/utils/file_id.py.
"""

from __future__ import annotations

import hashlib


def generate_file_id(content: str, source_path: str) -> str:
    """Generate hash ID from content and source path.

    Args:
        content: File content.
        source_path: Source path (used as salt for uniqueness).

    Returns:
        12-character hex hash ID (SHA-256 first 48 bits).
    """
    combined = f"{content}\n---\n{source_path}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]
