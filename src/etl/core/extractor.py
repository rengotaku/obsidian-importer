"""BaseExtractor - Template Method pattern for Extract stages.

Provides automatic chunking support for large conversations.
Only applies to Extract stages (Claude, ChatGPT, GitHub).
"""

from abc import abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import ProcessingItem
from .stage import BaseStage
from .status import ItemStatus
from .types import StageType


class BaseExtractor(BaseStage):
    """Abstract base class for Extract stages with chunking support.

    Implements Template Method pattern:
    1. discover_items() - concrete template method
    2. _discover_raw_items() - abstract (provider implements)
    3. _build_conversation_for_chunking() - abstract (provider implements)
    4. _chunk_if_needed() - concrete (automatic chunking)
    """

    def __init__(self, chunk_size: int = 25000):
        """Initialize BaseExtractor with chunker.

        Args:
            chunk_size: Character threshold for chunking (default 25000).
        """
        super().__init__()
        from ..utils.chunker import Chunker

        self._chunker = Chunker(chunk_size=chunk_size)

    @property
    def stage_type(self) -> StageType:
        """Type of this stage (always EXTRACT for extractors).

        Returns:
            StageType.EXTRACT
        """
        return StageType.EXTRACT

    @abstractmethod
    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover raw items from input path (provider-specific).

        This is the first hook in the Template Method pattern.
        Each provider implements this to locate and create initial ProcessingItems.

        Args:
            input_path: Path to input data (e.g., ZIP file, directory).

        Returns:
            Iterator of ProcessingItem instances (raw, before chunking).
        """
        ...

    @abstractmethod
    def _build_conversation_for_chunking(self, item: ProcessingItem) -> Any | None:
        """Build conversation object for chunking (provider-specific).

        This is the second hook in the Template Method pattern.
        Convert provider-specific data to ConversationProtocol for chunking.

        Args:
            item: ProcessingItem with provider-specific content.

        Returns:
            ConversationProtocol instance for chunking, or None to skip chunking.
        """
        ...

    def _build_chunk_messages(self, chunk: Any, conversation_dict: dict) -> list[dict] | None:
        """Build chat_messages for chunked conversation (provider-specific hook).

        This is the third hook in the Template Method pattern.
        Allows providers to customize chat_messages structure after chunking.

        Args:
            chunk: Chunked conversation object.
            conversation_dict: Original conversation dict (before chunking).

        Returns:
            List of message dicts to set in chunk_conv["chat_messages"], or None to preserve item.content.
        """
        return None

    def discover_items(self, input_path: Path, chunk: bool = True) -> Iterator[ProcessingItem]:
        """Discover items from input path (Template Method).

        This is the concrete template method that orchestrates:
        1. _discover_raw_items() - provider-specific discovery
        2. _chunk_if_needed() - automatic chunking if conversation exceeds threshold (if chunk=True)

        Args:
            input_path: Path to input data.
            chunk: Whether to enable chunking for large files (default: True for backward compat).

        Yields:
            ProcessingItem instances (possibly chunked via 1:N expansion).
        """
        raw_items = self._discover_raw_items(input_path)
        for item in raw_items:
            # Delegate to chunking logic (only if chunk=True)
            if chunk:
                chunked_items = self._chunk_if_needed(item)
                yield from chunked_items
            else:
                # No chunking - yield raw item
                item.metadata["is_chunked"] = False
                yield item

    def _chunk_if_needed(self, item: ProcessingItem) -> list[ProcessingItem]:
        """Check if item needs chunking and split if necessary (protected).

        This is the concrete implementation of chunking logic shared by all providers.

        Args:
            item: ProcessingItem to potentially chunk.

        Returns:
            List of ProcessingItems (single item if no chunking, multiple if chunked).
        """
        # Ask provider to build conversation for chunking
        conversation = self._build_conversation_for_chunking(item)

        # Provider returns None → skip chunking
        if conversation is None:
            return [item]

        # Check if chunking is needed
        if not self._chunker.should_chunk(conversation):
            # No chunking needed - mark as non-chunked
            item.metadata["is_chunked"] = False
            return [item]

        # Split conversation into chunks
        chunked = self._chunker.split(conversation)
        chunk_items = []

        # Parse original content as conversation dict
        import json

        conversation_dict = json.loads(item.content)

        for chunk_index, chunk_obj in enumerate(chunked.chunks):
            # Create a copy of the conversation dict for this chunk
            chunk_conv = dict(conversation_dict)

            # Call hook to build chunk-specific chat_messages
            messages = self._build_chunk_messages(chunk_obj, chunk_conv)
            if messages is not None:
                chunk_conv["chat_messages"] = messages

            # Serialize chunk conversation back to JSON
            chunk_content = json.dumps(chunk_conv, ensure_ascii=False)

            # Create new ProcessingItem for this chunk
            chunk_item = ProcessingItem(
                item_id=f"{item.item_id}_chunk_{chunk_index}",
                source_path=item.source_path,
                current_step=item.current_step,
                status=ItemStatus.PENDING,
                metadata={
                    **item.metadata,
                    "is_chunked": True,
                    "parent_item_id": item.item_id,
                    "chunk_index": chunk_index,
                    "total_chunks": len(chunked.chunks),
                },
                content=chunk_content,  # Use updated chunk content
            )
            chunk_items.append(chunk_item)

        return chunk_items
