"""Conversation chunker for obsidian-etl.

Splits large conversations at message boundaries with overlap.
Pure function interface for Kedro integration.
Migrated from src/etl/utils/chunker.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkInfo:
    """Information about a conversation chunk."""

    index: int
    messages: list[dict]
    char_count: int
    has_overlap: bool
    overlap_count: int


def should_chunk(messages: list[dict], chunk_size: int = 25000) -> bool:
    """Check if conversation needs chunking.

    Args:
        messages: List of message dicts with 'content' key.
        chunk_size: Character threshold for chunking.

    Returns:
        True if total characters >= chunk_size.
    """
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return total_chars >= chunk_size


def split_messages(
    messages: list[dict],
    chunk_size: int = 25000,
    overlap_messages: int = 2,
) -> list[ChunkInfo]:
    """Split messages into chunks at message boundaries.

    Args:
        messages: List of message dicts with 'content' and 'role' keys.
        chunk_size: Character threshold per chunk.
        overlap_messages: Number of messages to overlap between chunks.

    Returns:
        List of ChunkInfo objects.

    Raises:
        ValueError: If messages is empty.
    """
    if not messages:
        raise ValueError("Messages list is empty")

    chunks: list[ChunkInfo] = []
    current_messages: list[dict] = []
    current_chars = 0

    for message in messages:
        msg_chars = len(message.get("content", ""))

        # Single message exceeds chunk_size
        if msg_chars >= chunk_size and not current_messages:
            logger.warning(f"Single message exceeds chunk_size ({chunk_size}): {msg_chars} chars")
            chunks.append(
                ChunkInfo(
                    index=len(chunks),
                    messages=[message],
                    char_count=msg_chars,
                    has_overlap=len(chunks) > 0,
                    overlap_count=0,
                )
            )
            continue

        # Chunk boundary exceeded
        if current_chars + msg_chars > chunk_size and current_messages:
            overlap_count = min(overlap_messages, len(current_messages)) if chunks else 0

            chunks.append(
                ChunkInfo(
                    index=len(chunks),
                    messages=list(current_messages),
                    char_count=current_chars,
                    has_overlap=len(chunks) > 0,
                    overlap_count=overlap_count,
                )
            )

            # Set up overlap for next chunk
            if overlap_messages > 0 and current_messages:
                overlap_msgs = current_messages[-overlap_messages:]
                current_messages = list(overlap_msgs)
                current_chars = sum(len(m.get("content", "")) for m in current_messages)
            else:
                current_messages = []
                current_chars = 0

        current_messages.append(message)
        current_chars += msg_chars

    # Remaining messages
    if current_messages:
        overlap_count = min(overlap_messages, len(current_messages)) if chunks else 0
        chunks.append(
            ChunkInfo(
                index=len(chunks),
                messages=list(current_messages),
                char_count=current_chars,
                has_overlap=len(chunks) > 0,
                overlap_count=overlap_count,
            )
        )

    return chunks


def get_chunk_filename(title: str, chunk_index: int) -> str:
    """Generate chunk filename.

    Args:
        title: Original conversation title.
        chunk_index: Chunk number (0-indexed).

    Returns:
        Filename with 3-digit zero-padded suffix.
    """
    return f"{title}_{chunk_index + 1:03d}"
