"""KnowledgeTransformer stage for ETL pipeline.

Transforms Claude conversation data into knowledge notes.
Uses Ollama for LLM-based knowledge extraction.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.etl.core.stage import StageContext

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.etl.core.errors import StepError
from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.status import ItemStatus
from src.etl.core.types import StageType
from src.etl.utils.knowledge_extractor import (
    ExtractionResult,
    KnowledgeDocument,
    KnowledgeExtractor,
)

# =============================================================================
# Protocol for conversation data (used by KnowledgeExtractor)
# =============================================================================


@dataclass
class Message:
    """Simple message class conforming to MessageProtocol."""

    content: str
    _role: str

    @property
    def role(self) -> str:
        return self._role


@dataclass
class ConversationData:
    """Conversation data conforming to ConversationProtocol."""

    title: str
    created_at: str
    _messages: list[Message]
    _id: str
    _provider: str
    summary: str | None = None

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def id(self) -> str:
        return self._id

    @property
    def provider(self) -> str:
        return self._provider


class ExtractKnowledgeStep(BaseStep):
    """Extract knowledge from conversation content using Ollama.

    Uses KnowledgeExtractor to call Ollama API and extract structured
    knowledge from conversation data. Supports chunking for large conversations.
    """

    # Default chunk size threshold (characters)
    CHUNK_SIZE = 25000

    def __init__(self, chunk_size: int = CHUNK_SIZE, fetch_titles: bool = True):
        """Initialize ExtractKnowledgeStep with KnowledgeExtractor.

        Args:
            chunk_size: Threshold for chunking (default 25000 chars).
            fetch_titles: Enable URL title fetching (default: True).
        """
        self._extractor = KnowledgeExtractor(chunk_size=chunk_size, fetch_titles=fetch_titles)
        self._chunk_size = chunk_size
        self._pending_expansion: list[ProcessingItem] | None = None

    @property
    def name(self) -> str:
        return "extract_knowledge"

    def _translate_if_english(
        self, item: ProcessingItem, data: dict
    ) -> tuple[str | None, str | None]:
        """Translate summary if it's in English.

        T050: Detects English summary and translates to Japanese.

        Args:
            item: ProcessingItem with conversation data.
            data: Parsed conversation JSON.

        Returns:
            Tuple of (translated_summary, original_summary).
            If not English or translation fails, returns (None, original_summary).
        """
        original_summary = data.get("summary")

        if not original_summary:
            return None, None

        # Check if English
        if not self._extractor.is_english_summary(original_summary):
            return None, None

        # Attempt translation
        translated, error = self._extractor.translate_summary(original_summary)

        if error:
            # T053: Translation error - raise StepError for consistency
            raise StepError(
                f"Summary translation failed: {error}",
                item_id=item.item_id,
            )

        return translated, original_summary

    def _calculate_llm_context_size(self, data: dict) -> int:
        """Calculate the actual LLM context size from conversation data.

        Calculates the size of the context that will be sent to the LLM,
        based on the actual message text fields rather than the full JSON.

        Formula:
            LLM_context_size = HEADER (200) + sum(msg.text) + LABEL (15) * msg_count

        Args:
            data: Parsed conversation JSON.

        Returns:
            Estimated LLM context size (characters).
        """
        HEADER_SIZE = 200  # Fixed header (~200 chars)
        LABEL_OVERHEAD = 15  # "[User]\n" or "[Assistant]\n" + newline

        messages = data.get("chat_messages", [])

        # Sum of message text fields
        message_size = sum(
            len(msg.get("text", "") or "")  # Handle None
            for msg in messages
        )

        # Label overhead per message
        label_size = len(messages) * LABEL_OVERHEAD

        return HEADER_SIZE + message_size + label_size

    def _is_already_processed(self, item: ProcessingItem) -> bool:
        """Check if item has already been processed with knowledge extraction.

        Args:
            item: ProcessingItem to check.

        Returns:
            True if item has knowledge_extracted=True and knowledge_document is not None.
        """
        knowledge_extracted = item.metadata.get("knowledge_extracted")
        knowledge_document = item.metadata.get("knowledge_document")
        return knowledge_extracted is True and knowledge_document is not None

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Extract knowledge from conversation using Ollama.

        T034: Simplified to handle chunk metadata passthrough only.
        Chunking now happens at ImportPhase.discover_items() level.

        T065: Threshold check - skip LLM if content exceeds threshold and chunk=False.

        Args:
            item: Item with conversation content (may already be chunked).

        Returns:
            Item with extracted knowledge document in metadata.

        Raises:
            RuntimeError: If extraction fails.
        """
        # Skip already processed items (Resume mode optimization)
        if self._is_already_processed(item):
            item.status = ItemStatus.FILTERED
            item.metadata["skipped_reason"] = "already_processed"
            item.transformed_content = item.content
            return item

        source_type = item.metadata.get("source_type", "")

        # Only process conversations
        if source_type != "conversation":
            # Non-conversation items pass through
            item.transformed_content = item.content
            item.metadata["knowledge_extracted"] = False
            # T034: Preserve chunk metadata if present, otherwise set to False
            if "is_chunked" not in item.metadata:
                item.metadata["is_chunked"] = False
            return item

        # T065: Threshold check - skip LLM if content exceeds threshold and chunk=False
        chunk_enabled = item.metadata.get("chunk_enabled", False)
        is_chunked = item.metadata.get("is_chunked", False)

        # Parse conversation content first (for LLM context size calculation)
        if not item.content:
            item.metadata["knowledge_extracted"] = False
            # T034: Preserve chunk metadata if present, otherwise set to False
            if "is_chunked" not in item.metadata:
                item.metadata["is_chunked"] = False
            return item

        # Parse JSON once and reuse it
        data = None

        # Check LLM context size (skip if > threshold and chunk not enabled and not already chunked)
        if not chunk_enabled and not is_chunked:
            try:
                data = json.loads(item.content)
            except json.JSONDecodeError as e:
                # Import here to avoid circular dependency with linter
                from src.etl.core.errors import StepError

                raise StepError(f"JSON parse error: {e}", item_id=item.item_id) from e

            # Calculate actual LLM context size (not JSON size)
            llm_context_size = self._calculate_llm_context_size(data)
            if llm_context_size > self._chunk_size:
                # Skip LLM processing, mark as too_large
                item.status = ItemStatus.FILTERED
                item.metadata["skipped_reason"] = "too_large"
                item.metadata["too_large"] = True
                item.metadata["knowledge_extracted"] = False
                item.metadata["is_chunked"] = False
                item.transformed_content = item.content
                return item

        # Parse JSON if not already parsed (bypassed too_large check)
        if data is None:
            try:
                data = json.loads(item.content)
            except json.JSONDecodeError as e:
                # Import here to avoid circular dependency with linter
                from src.etl.core.errors import StepError

                raise StepError(f"JSON parse error: {e}", item_id=item.item_id) from e

        # T034: Chunk metadata already set by discover_items(), just preserve it
        # No need to check _should_chunk() - chunking happens at discover phase

        # Attempt translation before extraction
        translated_summary, original_summary = self._translate_if_english(item, data)

        # Set translation metadata
        if original_summary is not None:
            item.metadata["original_summary"] = original_summary
            if translated_summary is not None:
                item.metadata["summary_translated"] = True
            else:
                # Translation failed, use original
                item.metadata["summary_translated"] = False

        # Build conversation object for extractor
        conversation = self._build_conversation(data, item)

        # Call KnowledgeExtractor.extract() with tenacity retry
        result = self._extract_with_retry(conversation)

        if not result.success:
            # Handle Ollama error
            error_msg = result.error or "Unknown extraction error"
            item.metadata["knowledge_extracted"] = False
            item.metadata["extraction_error"] = error_msg
            item.metadata["llm_prompt"] = result.user_prompt
            item.metadata["llm_raw_response"] = result.raw_response

            # Import here to avoid circular dependency with linter
            from src.etl.core.errors import StepError

            raise StepError(
                f"Knowledge extraction failed: {error_msg}", item_id=item.item_id
            ) from None

        # Set metadata keys
        item.metadata["knowledge_extracted"] = True
        item.metadata["knowledge_document"] = result.document

        # Apply translation to document if available
        if translated_summary is not None and result.document:
            result.document.summary = translated_summary

        item.transformed_content = item.content  # Keep original for now

        return item

    def _build_conversation(self, data: dict, item: ProcessingItem) -> ConversationData:
        """Build ConversationData from JSON data.

        Args:
            data: Parsed conversation JSON.
            item: ProcessingItem for metadata.

        Returns:
            ConversationData object.
        """
        # Parse messages
        messages = []
        for msg in data.get("chat_messages", []):
            sender = msg.get("sender", "unknown")
            role = "user" if sender == "human" else "assistant"
            content = msg.get("text", "")
            messages.append(Message(content=content, _role=role))

        return ConversationData(
            title=data.get("name", item.metadata.get("conversation_name", "Untitled")),
            created_at=data.get("created_at", ""),
            _messages=messages,
            _id=data.get("uuid", item.item_id),
            _provider=item.metadata["source_provider"],  # Required, no fallback
            summary=data.get("summary"),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _extract_with_retry(self, conversation: ConversationData) -> ExtractionResult:
        """Extract knowledge with tenacity retry.

        Args:
            conversation: Conversation data.

        Returns:
            ExtractionResult from KnowledgeExtractor.
        """
        return self._extractor.extract(conversation)


class GenerateMetadataStep(BaseStep):
    """Generate metadata for knowledge note including item_id."""

    @property
    def name(self) -> str:
        return "generate_metadata"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Generate metadata for the knowledge note.

        T030: Use item.item_id (already generated from content hash).

        Args:
            item: Item with extracted knowledge.

        Returns:
            Item with generated metadata including item_id.
        """
        source_type = item.metadata.get("source_type", "unknown")

        # T030: Use item_id (already generated as content hash)
        item_id = item.item_id
        item.metadata["item_id"] = item_id

        # Update knowledge_document with item_id if present
        knowledge_doc = item.metadata.get("knowledge_document")
        if knowledge_doc and isinstance(knowledge_doc, KnowledgeDocument):
            knowledge_doc.item_id = item_id

        if source_type == "conversation":
            # Use knowledge_document if available
            if knowledge_doc and isinstance(knowledge_doc, KnowledgeDocument):
                item.metadata["generated_metadata"] = {
                    "title": knowledge_doc.title,
                    "uuid": knowledge_doc.source_conversation,
                    "created": knowledge_doc.created,
                    "summary": knowledge_doc.summary,
                    "tags": ["claude-export"],
                    "source_provider": item.metadata["source_provider"],  # Required, no fallback
                    "item_id": item_id,
                }
            else:
                # Fallback to item metadata
                item.metadata["generated_metadata"] = {
                    "title": item.metadata.get("conversation_name", "Untitled"),
                    "uuid": item.metadata.get("conversation_uuid", item.item_id),
                    "created": self._format_date(item.metadata.get("created_at")),
                    "updated": self._format_date(item.metadata.get("updated_at")),
                    "tags": ["claude-export"],
                    "source_provider": item.metadata["source_provider"],  # Required, no fallback
                    "item_id": item_id,
                }
        else:
            # Other files (memories, projects, etc.)
            item.metadata["generated_metadata"] = {
                "title": source_type.title(),
                "tags": ["claude-export", source_type],
                "item_id": item_id,
            }

        return item

    def _format_date(self, date_str: str | None) -> str:
        """Format ISO date string to YYYY-MM-DD."""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return datetime.now().strftime("%Y-%m-%d")


class FormatMarkdownStep(BaseStep):
    """Format content as Markdown."""

    @property
    def name(self) -> str:
        return "format_markdown"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Format transformed content as Markdown.

        T031: Use KnowledgeDocument.to_markdown() for conversations.

        For conversations: uses KnowledgeDocument.to_markdown().
        For other files: passes through as JSON without Markdown conversion.

        Args:
            item: Item with transformed content.

        Returns:
            Item with Markdown-formatted content (conversations only).
        """
        source_type = item.metadata.get("source_type", "")

        # GitHub Jekyll: already formatted with frontmatter, pass through
        if source_type == "github_jekyll":
            # Content is already in Markdown format with Obsidian frontmatter
            item.transformed_content = item.content
            item.metadata["formatted"] = True
            return item

        # Only format conversations as Markdown
        if source_type != "conversation":
            # Non-conversation items: use generic Markdown formatter
            content = item.transformed_content or item.content or ""
            markdown = self._format_generic(item, content)
            item.transformed_content = markdown
            item.metadata["formatted"] = True
            return item

        # T031: Use KnowledgeDocument.to_markdown() if available
        knowledge_doc = item.metadata.get("knowledge_document")
        if knowledge_doc and isinstance(knowledge_doc, KnowledgeDocument):
            markdown = knowledge_doc.to_markdown()
            # T066: Add too_large to frontmatter if present
            if item.metadata.get("too_large", False):
                markdown = self._add_too_large_to_frontmatter(markdown)
            item.transformed_content = markdown
            item.metadata["formatted"] = True
            return item

        # Fallback for conversation missing knowledge_document
        content = item.transformed_content or item.content or ""
        markdown = self._format_conversation(item, content)
        # T066: Add too_large to frontmatter if present
        if item.metadata.get("too_large", False):
            markdown = self._add_too_large_to_frontmatter(markdown)
        item.transformed_content = markdown
        item.metadata["formatted"] = True

        return item

    def _format_conversation(self, item: ProcessingItem, content: str) -> str:
        """Format conversation as Markdown (fallback).

        Args:
            item: ProcessingItem with metadata.
            content: JSON string of conversation data.

        Returns:
            Markdown string.
        """
        lines = []
        metadata = item.metadata.get("generated_metadata", {})

        # Frontmatter
        lines.append("---")
        lines.append(f"title: {metadata.get('title', 'Untitled')}")
        lines.append(f"uuid: {metadata.get('uuid', item.item_id)}")
        lines.append(f"created: {metadata.get('created', '')}")
        lines.append(f"updated: {metadata.get('updated', '')}")
        if metadata.get("item_id"):
            lines.append(f"item_id: {metadata['item_id']}")
        lines.append("tags:")
        for tag in metadata.get("tags", ["claude-export"]):
            lines.append(f"  - {tag}")
        lines.append("---")
        lines.append("")

        # Parse conversation data
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            lines.append("## Content")
            lines.append("")
            lines.append(content)
            return "\n".join(lines)

        # Summary (if present)
        summary = data.get("summary", "")
        if summary:
            lines.append("## Summary")
            lines.append("")
            lines.append(summary)
            lines.append("")

        # Conversation
        messages = data.get("chat_messages", [])
        if messages:
            lines.append("## 会話")
            lines.append("")

            for msg in messages:
                sender = msg.get("sender", "unknown")
                role_label = "**User**" if sender == "human" else "**Assistant**"
                lines.append(f"{role_label}:")
                lines.append("")

                # Get message text
                text = msg.get("text", "")
                if text:
                    lines.append(text.strip())
                    lines.append("")

        return "\n".join(lines)

    def _format_generic(self, item: ProcessingItem, content: str) -> str:
        """Format non-conversation content as Markdown.

        Args:
            item: ProcessingItem with metadata.
            content: Content string (may be JSON).

        Returns:
            Markdown string.
        """
        lines = []
        metadata = item.metadata.get("generated_metadata", {})

        # Frontmatter
        lines.append("---")
        lines.append(f"title: {metadata.get('title', 'Untitled')}")
        if metadata.get("item_id"):
            lines.append(f"item_id: {metadata['item_id']}")
        lines.append("tags:")
        for tag in metadata.get("tags", []):
            lines.append(f"  - {tag}")
        lines.append("normalized: true")
        lines.append("---")
        lines.append("")

        # Content
        lines.append(f"# {metadata.get('title', 'Content')}")
        lines.append("")

        # If JSON, format it nicely
        if content.startswith("{") or content.startswith("["):
            try:
                data = json.loads(content)
                lines.append("```json")
                lines.append(json.dumps(data, indent=2, ensure_ascii=False))
                lines.append("```")
            except json.JSONDecodeError:
                lines.append(content)
        else:
            lines.append(content)

        return "\n".join(lines)

    def _add_too_large_to_frontmatter(self, markdown: str) -> str:
        """Add too_large: true to frontmatter.

        T066: Inserts too_large field before closing --- of frontmatter.

        Args:
            markdown: Markdown content with frontmatter.

        Returns:
            Markdown with too_large field added.
        """
        if not markdown.startswith("---"):
            # No frontmatter, add it
            return f"---\ntoo_large: true\n---\n\n{markdown}"

        # Find end of frontmatter
        end_idx = markdown.find("---", 3)
        if end_idx == -1:
            # Invalid frontmatter, add field at end
            return markdown + "\ntoo_large: true"

        # Insert too_large before closing ---
        before = markdown[:end_idx]
        after = markdown[end_idx:]

        return f"{before}too_large: true\n{after}"


class KnowledgeTransformer(BaseStage):
    """Transform stage for knowledge extraction.

    T032: Removed custom run() method - now uses BaseStage.run().
    Chunking now happens at ImportPhase.discover_items() level.

    Transforms Claude conversation data into knowledge notes.
    """

    def __init__(self, steps: list[BaseStep] | None = None, fetch_titles: bool = True):
        """Initialize KnowledgeTransformer.

        Args:
            steps: Optional custom steps. Defaults to standard transformation steps.
            fetch_titles: Enable URL title fetching (default: True).
        """
        super().__init__()
        self._steps = steps or [
            ExtractKnowledgeStep(fetch_titles=fetch_titles),
            GenerateMetadataStep(),
            FormatMarkdownStep(),
        ]

    @property
    def stage_type(self) -> StageType:
        return StageType.TRANSFORM

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps

    # T032: Custom run() method REMOVED - using BaseStage.run() instead
    # Chunking logic moved to ImportPhase.discover_items()
    # T036: run_with_skip() method removed - Resume logic now in BaseStage.run()
