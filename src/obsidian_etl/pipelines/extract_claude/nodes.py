"""Nodes for Claude Extract pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from obsidian_etl.utils.chunker import should_chunk, split_messages
from obsidian_etl.utils.file_id import generate_file_id

logger = logging.getLogger(__name__)

MIN_MESSAGES = 3  # Minimum messages required for a valid conversation
MIN_CONTENT_LENGTH = 10  # Minimum content length after processing


def parse_claude_json(
    conversations: list[dict], existing_output: dict[str, callable] | None = None
) -> dict[str, dict]:
    """Parse Claude export JSON conversations to ParsedItem format.

    Args:
        conversations: List of Claude conversation dicts from conversations.json.
        existing_output: DEPRECATED - not used. Parse always processes all conversations.
                        Transform nodes handle resume logic instead.

    Returns:
        Dict mapping partition_id (file_id or file_id_chunkN) to ParsedItem dict.

    ParsedItem structure (see data-model.md E-2):
        - item_id: str (conversation uuid or file_id for chunks)
        - source_provider: "claude"
        - source_path: str (virtual path)
        - conversation_name: str | None
        - created_at: str | None
        - messages: list[dict] with {role, content}
        - content: str (formatted conversation text)
        - file_id: str (SHA256 12-char hash)
        - is_chunked: bool
        - chunk_index: int | None
        - total_chunks: int | None
        - parent_item_id: str | None
    """
    if not conversations:
        return {}

    # Note: existing_output parameter is kept for backward compatibility but not used.
    # Parse stage always processes all input. Resume logic is handled by Transform nodes.

    result = {}

    for conv in conversations:
        # Validate structure (uuid and chat_messages required)
        if not _validate_structure(conv):
            logger.debug("Skipping conversation: missing required fields (uuid or chat_messages)")
            continue

        conv_uuid = conv["uuid"]
        conv_name = conv.get("name")
        created_at = conv.get("created_at")
        raw_messages = conv["chat_messages"]

        # Filter out empty messages
        filtered_messages = [msg for msg in raw_messages if msg.get("text", "").strip()]

        # Validate minimum message count
        if len(filtered_messages) < MIN_MESSAGES:
            logger.debug(
                f"Skipping conversation {conv_uuid}: too few messages ({len(filtered_messages)} < {MIN_MESSAGES})"
            )
            continue

        # Normalize messages to {role, content} format
        normalized_messages = [
            {"role": msg["sender"], "content": msg["text"]} for msg in filtered_messages
        ]

        # Generate formatted content
        content = _format_conversation_content(normalized_messages)

        # Validate content length
        if len(content) < MIN_CONTENT_LENGTH:
            logger.debug(
                f"Skipping conversation {conv_uuid}: content too short ({len(content)} < {MIN_CONTENT_LENGTH})"
            )
            continue

        # Fallback conversation name if missing
        if not conv_name:
            conv_name = _fallback_conversation_name(normalized_messages)

        # Generate file_id
        virtual_path = f"conversations/{conv_uuid}.md"
        file_id = generate_file_id(content, virtual_path)

        # Check if chunking needed
        if should_chunk(normalized_messages):
            # Chunk and create multiple ParsedItems
            chunks = split_messages(normalized_messages)
            parent_item_id = file_id
            total_chunks = len(chunks)

            for chunk_info in chunks:
                chunk_messages = chunk_info.messages
                chunk_content = _format_conversation_content(chunk_messages)
                chunk_file_id = generate_file_id(
                    chunk_content, f"{virtual_path}_chunk{chunk_info.index}"
                )

                chunk_item = {
                    "item_id": chunk_file_id,
                    "source_provider": "claude",
                    "source_path": virtual_path,
                    "conversation_name": conv_name,
                    "created_at": created_at,
                    "messages": chunk_messages,
                    "content": chunk_content,
                    "file_id": chunk_file_id,
                    "is_chunked": True,
                    "chunk_index": chunk_info.index,
                    "total_chunks": total_chunks,
                    "parent_item_id": parent_item_id,
                }

                partition_id = f"{parent_item_id}_chunk{chunk_info.index}"
                result[partition_id] = chunk_item

        else:
            # Single item (no chunking)
            parsed_item = {
                "item_id": conv_uuid,
                "source_provider": "claude",
                "source_path": virtual_path,
                "conversation_name": conv_name,
                "created_at": created_at,
                "messages": normalized_messages,
                "content": content,
                "file_id": file_id,
                "is_chunked": False,
                "chunk_index": None,
                "total_chunks": None,
                "parent_item_id": None,
            }

            result[file_id] = parsed_item

    return result


def _validate_structure(conv: dict) -> bool:
    """Validate conversation has required fields.

    Args:
        conv: Conversation dict.

    Returns:
        True if uuid and chat_messages are present.
    """
    return "uuid" in conv and "chat_messages" in conv


def _format_conversation_content(messages: list[dict]) -> str:
    """Format messages into conversation text.

    Args:
        messages: List of message dicts with {role, content}.

    Returns:
        Formatted conversation string with "Human:" and "Assistant:" prefixes.
    """
    lines = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        # Capitalize role for display
        role_label = "Human" if role == "human" else "Assistant"
        lines.append(f"{role_label}: {content}")

    return "\n\n".join(lines)


def _fallback_conversation_name(messages: list[dict]) -> str:
    """Generate fallback conversation name from first user message.

    Args:
        messages: List of message dicts with {role, content}.

    Returns:
        First user message (truncated to 50 chars) or "Untitled".
    """
    for msg in messages:
        if msg["role"] == "human":
            first_message = msg["content"].strip()
            if first_message:
                # Truncate to 50 chars for readability
                return first_message[:50]

    return "Untitled"
