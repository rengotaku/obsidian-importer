"""Nodes for OpenAI (ChatGPT) Extract pipeline."""

from __future__ import annotations

import io
import json
import logging
import zipfile
from datetime import UTC, datetime

from obsidian_etl.utils.chunker import should_chunk, split_messages
from obsidian_etl.utils.file_id import generate_file_id
from obsidian_etl.utils.timing import timed_node

logger = logging.getLogger(__name__)

MIN_MESSAGES = 3  # Minimum messages required for a valid conversation


@timed_node
def parse_chatgpt_zip(
    partitioned_input: dict[str, callable],
    params: dict | None = None,
    existing_output: dict[str, callable] | None = None,
) -> dict[str, dict]:
    """Parse ChatGPT export ZIP to ParsedItem format.

    Extracts conversations.json from ZIP, traverses ChatGPT mapping tree,
    converts to unified ParsedItem format with multimodal handling and chunking.

    Args:
        partitioned_input: Dict of filename -> Callable returning ZIP bytes.
        params: Pipeline parameters (unused, for interface consistency).
        existing_output: DEPRECATED - not used. Parse always processes all conversations.
                        Transform nodes handle resume logic instead.

    Returns:
        Dict mapping partition_id (file_id or file_id_chunkN) to ParsedItem dict.

    ParsedItem structure (see data-model.md E-2):
        - item_id: str (conversation id or file_id for chunks)
        - source_provider: "openai"
        - source_path: str (ZIP filename)
        - conversation_name: str | None
        - created_at: str | None (ISO 8601)
        - messages: list[dict] with {role, content}
        - content: str (formatted conversation text)
        - file_id: str (SHA256 12-char hash)
        - is_chunked: bool
        - chunk_index: int | None
        - total_chunks: int | None
        - parent_item_id: str | None
    """
    if not partitioned_input:
        return {}

    # Note: existing_output parameter is kept for backward compatibility but not used.
    # Parse stage always processes all input. Resume logic is handled by Transform nodes.

    result = {}

    for zip_name, load_func in partitioned_input.items():
        try:
            zip_bytes = load_func()
        except Exception as e:
            logger.warning(f"Failed to load ZIP {zip_name}: {e}")
            continue

        # Extract conversations.json from ZIP
        try:
            conversations_data = _extract_conversations_from_zip(zip_bytes)
        except Exception as e:
            logger.warning(f"Failed to extract conversations from {zip_name}: {e}")
            continue

        if not conversations_data:
            logger.debug(f"No conversations found in {zip_name}")
            continue

        # Process each conversation
        for conv in conversations_data:
            # Validate required fields
            if not _validate_conversation_structure(conv):
                logger.debug("Skipping conversation: missing required fields (id or mapping)")
                continue

            conv_id = conv["id"]
            title = conv.get("title")
            create_time = conv.get("create_time")
            mapping = conv["mapping"]
            current_node = conv.get("current_node", "")

            # Traverse mapping tree to extract messages
            messages = _traverse_messages(mapping, current_node)

            if len(messages) < MIN_MESSAGES:
                logger.debug(
                    f"Skipping conversation {conv_id}: too few messages ({len(messages)} < {MIN_MESSAGES})"
                )
                continue

            # Fallback title if missing
            if not title:
                title = _fallback_conversation_name(messages)

            # Convert timestamp
            created_at = _convert_timestamp(create_time)

            # Generate formatted content
            content = _format_conversation_content(messages)

            # Generate file_id
            virtual_path = f"conversations/{conv_id}.md"
            file_id = generate_file_id(content, virtual_path)

            # Check if chunking needed
            if should_chunk(messages):
                # Chunk and create multiple ParsedItems
                chunks = split_messages(messages)
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
                        "source_provider": "openai",
                        "source_path": zip_name,
                        "conversation_name": title,
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
                    "item_id": conv_id,
                    "source_provider": "openai",
                    "source_path": zip_name,
                    "conversation_name": title,
                    "created_at": created_at,
                    "messages": messages,
                    "content": content,
                    "file_id": file_id,
                    "is_chunked": False,
                    "chunk_index": None,
                    "total_chunks": None,
                    "parent_item_id": None,
                }

                result[file_id] = parsed_item

    return result


def _extract_conversations_from_zip(zip_bytes: bytes) -> list[dict]:
    """Extract conversations.json from ChatGPT export ZIP.

    Args:
        zip_bytes: ZIP file content as bytes.

    Returns:
        List of conversation dicts.

    Raises:
        ValueError: If conversations.json not found or invalid JSON.
    """
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf, "r") as zf:
        if "conversations.json" not in zf.namelist():
            raise ValueError("conversations.json not found in ZIP")

        conversations_json = zf.read("conversations.json")
        conversations = json.loads(conversations_json)

        if not isinstance(conversations, list):
            raise ValueError("conversations.json must contain a list")

        return conversations


def _validate_conversation_structure(conv: dict) -> bool:
    """Validate conversation has required fields.

    Args:
        conv: Conversation dict.

    Returns:
        True if id and mapping are present.
    """
    return "id" in conv and "mapping" in conv


def _traverse_messages(mapping: dict[str, dict], current_node: str) -> list[dict]:
    """Traverse ChatGPT mapping tree from current_node to root.

    ChatGPT conversations are stored as a tree structure where each node
    has a parent reference. This function follows the parent chain from
    current_node to the root, collecting messages along the way.

    Filters out system/tool roles and converts user → human.

    Args:
        mapping: ChatGPT mapping dict (node_id -> Node).
        current_node: Starting node ID (conversation endpoint).

    Returns:
        List of normalized messages {role, content} in chronological order.
    """
    raw_messages = []
    node_id = current_node

    # Traverse parent chain to collect messages
    while node_id:
        node = mapping.get(node_id, {})
        if node.get("message"):
            raw_messages.append(node["message"])
        node_id = node.get("parent")

    # Reverse to chronological order (oldest first)
    raw_messages.reverse()

    # Convert to normalized format
    normalized_messages = []
    for msg in raw_messages:
        author = msg.get("author", {})
        role = author.get("role", "")

        # Convert role
        converted_role = _convert_role(role)
        if converted_role is None:
            continue  # Skip system/tool messages

        # Extract text from parts
        content_obj = msg.get("content", {})
        parts = content_obj.get("parts", [])
        text = _extract_text_from_parts(parts)

        if not text.strip():
            continue

        normalized_messages.append({"role": converted_role, "content": text})

    return normalized_messages


def _convert_role(role: str) -> str | None:
    """Convert ChatGPT role to normalized role.

    Args:
        role: ChatGPT role (user, assistant, system, tool).

    Returns:
        Normalized role (human, assistant) or None if excluded.
    """
    role_mapping = {
        "user": "human",
        "assistant": "assistant",
    }
    return role_mapping.get(role)


def _extract_text_from_parts(parts: list[str | dict]) -> str:
    """Extract text content from ChatGPT content.parts array.

    ChatGPT messages can be multimodal (text + images + audio). This function
    extracts text content and creates placeholders for non-text content.

    Args:
        parts: List of content parts (str or dict).

    Returns:
        Combined text with placeholders for non-text content.
    """
    text_parts = []

    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict):
            content_type = part.get("content_type", "")
            if content_type == "image_asset_pointer":
                asset_pointer = part.get("asset_pointer", "unknown")
                text_parts.append(f"[Image: {asset_pointer}]")
            elif "audio" in content_type.lower():
                filename = (
                    part.get("filename")
                    or part.get("asset_pointer")
                    or part.get("name")
                    or "unknown"
                )
                text_parts.append(f"[Audio: {filename}]")
            else:
                # Fallback for any other multimodal content
                text_parts.append(f"[{content_type}]")

    return "\n".join(text_parts)


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


def _convert_timestamp(ts: float | None) -> str:
    """Convert Unix timestamp to ISO 8601 format.

    Args:
        ts: Unix timestamp (seconds since epoch) or None.

    Returns:
        ISO 8601 date string. Falls back to current datetime if ts is None.
    """
    dt = datetime.now(tz=UTC) if ts is None else datetime.fromtimestamp(ts, tz=UTC)
    return dt.isoformat()
