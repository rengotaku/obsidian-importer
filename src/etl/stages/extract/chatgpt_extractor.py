"""ChatGPTExtractor stage for ETL pipeline.

Extracts conversations from ChatGPT export ZIP files.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.etl.core.extractor import BaseExtractor
from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStep
from src.etl.core.status import ItemStatus
from src.etl.utils.file_id import generate_file_id
from src.etl.utils.zip_handler import read_conversations_from_zip

# Short conversation skip threshold (disabled - process all conversations)
MIN_MESSAGES = 1


@dataclass
class ChatGPTMessage:
    """Simple message wrapper for Chunker protocol (ChatGPT)."""

    content: str
    _role: str

    @property
    def role(self) -> str:
        return self._role


@dataclass
class ChatGPTConversation:
    """Simple conversation wrapper for Chunker protocol (ChatGPT)."""

    title: str
    created_at: str
    _messages: list
    _id: str
    _provider: str = "openai"

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def id(self) -> str:
        return self._id

    @property
    def provider(self) -> str:
        return self._provider


def traverse_messages(mapping: dict[str, Any], current_node: str) -> list[dict]:
    """Traverse ChatGPT mapping tree from current_node to root.

    ChatGPT conversations are stored as a tree structure where each node
    has a parent reference. This function follows the parent chain from
    current_node to the root, collecting messages along the way.

    Args:
        mapping: ChatGPT mapping dict (node_id -> Node).
        current_node: Starting node ID (conversation endpoint).

    Returns:
        List of messages in chronological order (oldest first).
    """
    messages = []
    node_id = current_node

    while node_id:
        node = mapping.get(node_id, {})
        if node.get("message"):
            messages.append(node["message"])
        node_id = node.get("parent")

    return list(reversed(messages))


def extract_text_from_parts(parts: list[str | dict]) -> str:
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
                # T043: Handle audio files as [Audio: filename] placeholder
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


def convert_role(role: str) -> str | None:
    """Convert ChatGPT role to Claude-compatible sender.

    Args:
        role: ChatGPT role (user, assistant, system, tool).

    Returns:
        Converted role (human, assistant) or None if excluded.
    """
    role_mapping = {
        "user": "human",
        "assistant": "assistant",
    }
    return role_mapping.get(role)


def convert_timestamp(ts: float | None) -> str:
    """Convert Unix timestamp to YYYY-MM-DD format.

    Args:
        ts: Unix timestamp (seconds since epoch) or None.

    Returns:
        Date string in YYYY-MM-DD format. Falls back to current date if ts is None.
    """
    if ts is None:
        # T070: Fallback to current date when timestamp is missing
        dt = datetime.now(tz=UTC)
    else:
        dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.strftime("%Y-%m-%d")


class ValidateMinMessagesStep(BaseStep):
    """Validate conversation has minimum number of messages.

    1:1 Step - Checks message count and sets status=SKIPPED if below threshold.
    """

    @property
    def name(self) -> str:
        return "validate_min_messages"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Validate message count and skip if below MIN_MESSAGES.

        Args:
            item: Item with content=Claude messages JSON.

        Returns:
            Item with status=PENDING or SKIPPED.
        """
        if item.content is None:
            raise ValueError("Item content is None, cannot validate messages")

        try:
            conversation_data = json.loads(item.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in conversation content: {e}")

        chat_messages = conversation_data.get("chat_messages", [])
        message_count = len(chat_messages)

        if message_count < MIN_MESSAGES:
            item.status = ItemStatus.FILTERED
            item.metadata["skip_reason"] = "skipped_short"
            item.metadata["message_count"] = message_count
        else:
            # Generate file_id from conversation content hash
            conversation_id = conversation_data.get("uuid", "")
            virtual_path = Path(f"conversations/{conversation_id}.md")
            item.item_id = generate_file_id(item.content, virtual_path)

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has content."""
        return item.content is not None


class ChatGPTExtractor(BaseExtractor):
    """Extract stage for ChatGPT export files.

    Discovers ZIP files and delegates processing to Steps:
    1. ValidateMinMessagesStep: Skip conversations below MIN_MESSAGES threshold

    ZIP reading, parsing, and format conversion are handled by _discover_raw_items().
    """

    @property
    def steps(self) -> list[BaseStep]:
        """Return ordered list of extraction steps.

        Returns:
            List of steps for ChatGPT extraction pipeline.
        """
        return [ValidateMinMessagesStep()]

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover and expand ChatGPT conversations from ZIP file.

        Implements BaseExtractor abstract method.
        Reads ZIP, extracts conversations.json, converts to Claude format,
        and yields one ProcessingItem per conversation.

        Args:
            input_path: Path to ChatGPT export ZIP file or directory containing ZIP.

        Yields:
            ProcessingItem for each conversation (Claude format, ready for chunking).
        """
        # Find ZIP file: accept direct ZIP path or directory containing ZIP
        zip_path = input_path
        if input_path.is_dir():
            zip_files = list(input_path.glob("*.zip"))
            if not zip_files:
                return
            zip_path = zip_files[0]  # Use first ZIP file found

        if not zip_path.exists():
            return

        # Read conversations from ZIP
        try:
            conversations_data = read_conversations_from_zip(zip_path)
        except Exception:
            # If ZIP reading fails, return empty
            return

        if not isinstance(conversations_data, list):
            return

        # Handle empty conversations.json
        if len(conversations_data) == 0:
            return

        # Expand to individual conversations
        for conv in conversations_data:
            conversation_id = conv.get("conversation_id") or conv.get("id")
            if not conversation_id:
                continue

            title = conv.get("title", "")
            create_time = conv.get("create_time")
            mapping = conv.get("mapping", {})
            current_node = conv.get("current_node", "")

            if not mapping or not current_node:
                continue

            # Traverse ChatGPT mapping tree to extract messages
            messages = traverse_messages(mapping, current_node)

            chat_messages = []
            for msg in messages:
                author = msg.get("author", {})
                role = author.get("role", "")

                sender = convert_role(role)
                if sender is None:
                    continue  # Skip system/tool messages

                content_obj = msg.get("content", {})
                parts = content_obj.get("parts", [])
                text = extract_text_from_parts(parts)

                if not text:
                    continue

                create_time_msg = msg.get("create_time", create_time)

                chat_messages.append(
                    {
                        "uuid": msg.get("id", ""),
                        "sender": sender,
                        "text": text,
                        "created_at": convert_timestamp(create_time_msg),
                    }
                )

            # Skip if no messages after filtering
            if len(chat_messages) < MIN_MESSAGES:
                continue

            # Generate title from first user message if missing
            if not title:
                first_user_msg = next(
                    (msg for msg in chat_messages if msg["sender"] == "human"), None
                )
                if first_user_msg:
                    title = first_user_msg["text"][:50].strip()
                    if len(first_user_msg["text"]) > 50:
                        title += "..."
                else:
                    title = "Untitled Conversation"

            # Fallback to current date if timestamp missing
            if create_time is None:
                created_at = datetime.now(UTC).strftime("%Y-%m-%d")
            else:
                created_at = convert_timestamp(create_time)

            # Build final conversation data (Claude format)
            final_conversation = {
                "uuid": conversation_id,
                "name": title,
                "created_at": created_at,
                "chat_messages": chat_messages,
            }

            # Generate file_id from conversation content hash
            conv_content = json.dumps(final_conversation, ensure_ascii=False)
            virtual_path = Path(f"conversations/{conversation_id}.md")
            file_id = generate_file_id(conv_content, virtual_path)

            # Yield ProcessingItem with Claude-format content
            yield ProcessingItem(
                item_id=file_id,
                source_path=zip_path,
                current_step="discover",
                status=ItemStatus.PENDING,
                metadata={
                    "conversation_uuid": conversation_id,
                    "conversation_name": title,
                    "created_at": created_at,
                    "source_provider": "openai",
                    "source_type": "conversation",
                    "message_count": len(chat_messages),
                    "format": "claude",
                },
                content=conv_content,
            )

    def _build_conversation_for_chunking(
        self, item: ProcessingItem
    ) -> "ChatGPTConversation | None":
        """Build conversation object for chunking from ProcessingItem.

        Implements BaseExtractor abstract method.
        Converts ProcessingItem content (Claude format after ConvertFormatStep)
        to ChatGPTConversation for Chunker.

        Args:
            item: ProcessingItem with conversation JSON (Claude format).

        Returns:
            ChatGPTConversation object for chunking, or None to skip chunking.
        """
        try:
            conv = json.loads(item.content)
        except (json.JSONDecodeError, TypeError):
            # Skip chunking if content is invalid
            return None

        # Build ChatGPTConversation for Chunker
        messages = []
        for msg in conv.get("chat_messages", []):
            messages.append(
                ChatGPTMessage(
                    content=msg.get("text", ""),
                    _role=msg.get("sender", "unknown"),
                )
            )

        return ChatGPTConversation(
            title=conv.get("name", "Untitled"),
            created_at=conv.get("created_at", ""),
            _messages=messages,
            _id=conv.get("uuid", ""),
            _provider="openai",
        )

    def _build_chunk_messages(self, chunk, conv_dict: dict) -> list[dict]:
        """Build chat_messages array for chunked conversation (ChatGPT format).

        Args:
            chunk: ChunkedConversation chunk from Chunker.
            conv_dict: Original conversation dict.

        Returns:
            List of chat_messages dicts with ChatGPT-specific fields.
        """
        return [
            {
                "uuid": "",
                "text": msg.content,
                "sender": msg.role,
                "created_at": conv_dict.get("created_at", ""),
            }
            for msg in chunk.messages
        ]
