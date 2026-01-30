"""ClaudeExtractor stage for ETL pipeline.

Extracts conversations from Claude export JSON files or ZIP archives.
"""

import json
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.etl.core.extractor import BaseExtractor
from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStep
from src.etl.core.status import ItemStatus
from src.etl.utils.file_id import generate_file_id


@dataclass
class SimpleMessage:
    """Simple message wrapper for Chunker protocol."""

    content: str
    _role: str

    @property
    def role(self) -> str:
        return self._role


@dataclass
class SimpleConversation:
    """Simple conversation wrapper for Chunker protocol."""

    title: str
    created_at: str
    _messages: list
    _id: str
    _provider: str = "claude"

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def id(self) -> str:
        return self._id

    @property
    def provider(self) -> str:
        return self._provider


class ParseJsonStep(BaseStep):
    """Parse Claude export JSON file or pass through pre-loaded content."""

    @property
    def name(self) -> str:
        return "parse_json"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Parse JSON file or use pre-loaded content.

        If content is already set (e.g., from expanded conversations),
        validates it as JSON and passes through.

        Args:
            item: Item with source_path or pre-loaded content.

        Returns:
            Item with content set to JSON string.
        """
        # Content already set from discover_items (expanded conversation)
        if item.content:
            # Validate it's valid JSON
            try:
                json.loads(item.content)
            except json.JSONDecodeError as e:
                item.metadata["parse_error"] = str(e)
            return item

        # Load from file
        with open(item.source_path, encoding="utf-8") as f:
            data = json.load(f)

        item.content = json.dumps(data, ensure_ascii=False)

        # Set source_type if not already set
        if "source_type" not in item.metadata:
            item.metadata["source_type"] = "claude_export"

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has JSON file or pre-loaded content."""
        if item.content:
            return True
        return item.source_path and item.source_path.suffix.lower() == ".json"


class ValidateStructureStep(BaseStep):
    """Validate Claude export structure."""

    @property
    def name(self) -> str:
        return "validate_structure"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Validate the structure of parsed JSON.

        Handles both:
        - Individual conversations (source_type=conversation)
        - Full export files (memories, projects, etc.)

        Args:
            item: Item with content set to JSON string.

        Returns:
            Item with validation metadata.
        """
        if item.content is None:
            item.metadata["valid_structure"] = False
            return item

        try:
            data = json.loads(item.content)
            source_type = item.metadata.get("source_type", "")

            if source_type == "conversation":
                # Validate conversation structure
                item.metadata["valid_structure"] = self._validate_conversation(data)
                item.metadata["message_count"] = len(data.get("chat_messages", []))
            elif isinstance(data, dict):
                item.metadata["valid_structure"] = True
                item.metadata["has_conversations"] = "conversations" in data
            else:
                item.metadata["valid_structure"] = True
                item.metadata["is_array"] = isinstance(data, list)
        except json.JSONDecodeError:
            item.metadata["valid_structure"] = False

        return item

    def _validate_conversation(self, data: dict) -> bool:
        """Validate individual conversation structure.

        Args:
            data: Conversation dict.

        Returns:
            True if valid conversation structure.
        """
        required_fields = ["uuid", "chat_messages"]
        return all(field in data for field in required_fields)


class ClaudeExtractor(BaseExtractor):
    """Extract stage for Claude export files.

    Parses Claude export JSON and extracts conversation data.
    """

    CHUNK_SIZE = 25000  # Default chunk threshold

    def __init__(
        self,
        steps: list[BaseStep] | None = None,
        chunk_size: int = CHUNK_SIZE,
    ):
        """Initialize ClaudeExtractor.

        Args:
            steps: Optional custom steps. Defaults to standard extraction steps.
            chunk_size: Threshold for chunking conversations (default 25000 chars).
        """
        super().__init__(chunk_size=chunk_size)
        self._steps = steps or [
            ParseJsonStep(),
            ValidateStructureStep(),
        ]

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover raw conversation items without chunking.

        Implements BaseExtractor abstract method.
        Extracts individual conversations from conversations.json.
        Chunking is delegated to BaseExtractor.discover_items() template method.

        Args:
            input_path: Directory containing Claude export JSON files,
                       or ZIP file containing conversations.json.

        Yields:
            ProcessingItem for each conversation (raw, before chunking).
        """
        if not input_path.exists():
            return

        # Determine source: ZIP file, directory with ZIP, or directory with JSON
        conversations: list
        source_path: Path

        if input_path.suffix.lower() == ".zip":
            # Direct ZIP file path
            source_path = input_path
            try:
                conversations = self._read_conversations_from_zip(input_path)
            except (KeyError, json.JSONDecodeError, zipfile.BadZipFile) as e:
                yield ProcessingItem(
                    item_id="conversations_error",
                    source_path=input_path,
                    current_step="discover",
                    status=ItemStatus.FAILED,
                    metadata={"error": str(e)},
                )
                return
        elif input_path.is_dir():
            # Directory: check for conversations.json first, then ZIP files
            conversations_file = input_path / "conversations.json"
            if conversations_file.exists():
                # Direct JSON file
                source_path = conversations_file
                try:
                    with open(conversations_file, encoding="utf-8") as f:
                        conversations = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    yield ProcessingItem(
                        item_id="conversations_error",
                        source_path=conversations_file,
                        current_step="discover",
                        status=ItemStatus.FAILED,
                        metadata={"error": str(e)},
                    )
                    return
            else:
                # Check for ZIP files in directory
                zip_files = list(input_path.glob("*.zip"))
                if not zip_files:
                    return  # No input files found
                source_path = zip_files[0]  # Use first ZIP file
                try:
                    conversations = self._read_conversations_from_zip(source_path)
                except (KeyError, json.JSONDecodeError, zipfile.BadZipFile) as e:
                    yield ProcessingItem(
                        item_id="conversations_error",
                        source_path=source_path,
                        current_step="discover",
                        status=ItemStatus.FAILED,
                        metadata={"error": str(e)},
                    )
                    return
        else:
            # Not a directory or ZIP file
            return

        if not isinstance(conversations, list):
            yield ProcessingItem(
                item_id="conversations_error",
                source_path=source_path,
                current_step="discover",
                status=ItemStatus.FAILED,
                metadata={"error": "conversations.json is not a list"},
            )
            return

        # Yield each conversation as a raw item (no chunking here)
        for conv in conversations:
            conv_uuid = conv.get("uuid", "unknown")
            conv_name = conv.get("name", "Untitled")
            conv_content = json.dumps(conv, ensure_ascii=False)

            # Generate item_id from content hash
            virtual_path = Path(f"conversations/{conv_uuid}.md")
            item_id = generate_file_id(conv_content, virtual_path)

            # Create raw ProcessingItem (chunking handled by BaseExtractor)
            yield ProcessingItem(
                item_id=item_id,
                source_path=source_path,
                current_step="init",
                status=ItemStatus.PENDING,
                content=conv_content,
                metadata={
                    "discovered_at": datetime.now().isoformat(),
                    "source_type": "conversation",
                    "conversation_name": conv_name,
                    "conversation_uuid": conv_uuid,
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "source_provider": "claude",
                },
            )

    def _read_conversations_from_zip(self, zip_path: Path) -> list:
        """Read conversations.json from Claude export ZIP file.

        Args:
            zip_path: Path to Claude export ZIP file.

        Returns:
            Parsed JSON list from conversations.json.

        Raises:
            FileNotFoundError: If ZIP file doesn't exist.
            KeyError: If conversations.json not found in ZIP.
            json.JSONDecodeError: If conversations.json is invalid JSON.
            zipfile.BadZipFile: If file is not a valid ZIP.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as zf:
            if "conversations.json" not in zf.namelist():
                raise KeyError(f"conversations.json not found in {zip_path}")

            with zf.open("conversations.json") as f:
                return json.load(f)

    def _build_conversation_for_chunking(self, item: ProcessingItem) -> SimpleConversation | None:
        """Build conversation object for chunking from ProcessingItem.

        Implements BaseExtractor abstract method.
        Converts ProcessingItem content to SimpleConversation for Chunker.

        Args:
            item: ProcessingItem with conversation JSON in content.

        Returns:
            SimpleConversation object for chunking, or None to skip chunking.
        """
        try:
            conv = json.loads(item.content)
        except (json.JSONDecodeError, TypeError):
            # Skip chunking if content is invalid
            return None

        # Build SimpleConversation for Chunker
        messages = []
        for msg in conv.get("chat_messages", []):
            messages.append(
                SimpleMessage(
                    content=msg.get("text", ""),
                    _role=msg.get("sender", "unknown"),
                )
            )

        return SimpleConversation(
            title=conv.get("name", "Untitled"),
            created_at=conv.get("created_at", ""),
            _messages=messages,
            _id=conv.get("uuid", "unknown"),
        )

    def _build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict]:
        """Build chat_messages for chunked conversation (Claude format).

        Implements BaseExtractor hook method.
        Claude conversations use simple {text, sender} format only.

        Args:
            chunk: Chunked conversation object.
            conversation_dict: Original conversation dict (not used for Claude).

        Returns:
            List of message dicts with only text and sender keys.
        """
        return [{"text": msg.content, "sender": msg.role} for msg in chunk.messages]
