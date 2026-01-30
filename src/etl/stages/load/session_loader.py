"""SessionLoader stage for ETL pipeline.

Loads processed items to session output folder.
"""

import logging
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.status import ItemStatus
from src.etl.core.types import StageType

logger = logging.getLogger(__name__)


class WriteToSessionStep(BaseStep):
    """Write processed content to session output folder."""

    def __init__(self, output_path: Path | None = None):
        """Initialize WriteToSessionStep.

        Args:
            output_path: Override output path. If None, uses context.
        """
        self._output_path = output_path

    @property
    def name(self) -> str:
        return "write_to_session"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Write content to session output folder.

        Only writes conversation items. Other items (memories, projects, users)
        are skipped.

        Args:
            item: Item with transformed content.

        Returns:
            Item with output_path set (if written) or skipped flag.
        """
        source_type = item.metadata.get("source_type", "")

        # Only write conversations and github_jekyll to output
        if source_type not in ("conversation", "github_jekyll"):
            item.metadata["skipped"] = True
            item.metadata["skip_reason"] = "non-conversation/non-jekyll data not written"
            return item

        # Skip writing if item was skipped in earlier stages
        if item.status == ItemStatus.FILTERED:
            item.metadata["skipped"] = True
            item.metadata["skip_reason"] = item.metadata.get(
                "skip_reason", "skipped in earlier stage"
            )
            return item

        content = item.transformed_content or item.content or ""

        # Determine output subfolder and filename
        subfolder = self._determine_subfolder(item)
        filename = self._determine_filename(item)

        # Use stored output path or item's output path
        output_path = self._output_path
        if output_path is None:
            # Fallback: use item_id as filename in current directory
            output_path = Path(".")

        # Add subfolder for organization
        output_file = output_path / subfolder / filename

        # Write content
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

        item.output_path = output_file
        item.metadata["written_to"] = str(output_file)

        return item

    def _determine_subfolder(self, item: ProcessingItem) -> str:
        """Determine output subfolder based on source type.

        Args:
            item: ProcessingItem to get subfolder for.

        Returns:
            Subfolder name (e.g., 'conversations', 'memories').
        """
        source_type = item.metadata.get("source_type", "")

        # Map source types to subfolders
        subfolder_map = {
            "conversation": "conversations",
            "memories": "memories",
            "projects": "projects",
            "users": "users",
        }

        return subfolder_map.get(source_type, "other")

    def _determine_filename(self, item: ProcessingItem) -> str:
        """Determine output filename for item.

        T035: Added chunk suffix support (_001, _002, etc.) for chunked items.

        For conversations: use conversation_name or item_id (UUID) with .md extension.
        For chunked conversations: append chunk suffix (_001, _002, etc.).
        For other files: use original filename with .json extension.

        Args:
            item: ProcessingItem to get filename for.

        Returns:
            Filename with appropriate extension (.md for conversations, .json for others).
        """
        source_type = item.metadata.get("source_type", "")

        if source_type == "conversation":
            # Use conversation name or UUID
            conv_name = item.metadata.get("conversation_name", "")
            if conv_name and conv_name != "Untitled":
                # Sanitize filename
                safe_name = self._sanitize_filename(conv_name)
                base_filename = safe_name
            else:
                base_filename = item.item_id

            # T035: Add chunk suffix if this is a chunked item
            is_chunked = item.metadata.get("is_chunked", False)
            if is_chunked:
                chunk_index = item.metadata.get("chunk_index", 0)
                # 1-indexed, 3-digit zero-padded (e.g., _001, _002)
                chunk_suffix = f"_{chunk_index + 1:03d}"
                return f"{base_filename}{chunk_suffix}.md"

            return f"{base_filename}.md"

        elif source_type == "github_jekyll":
            # GitHub Jekyll: use metadata title or source filename with .md extension
            title = item.metadata.get("title", "")
            if title:
                safe_name = self._sanitize_filename(title)
                return f"{safe_name}.md"
            # Fallback to source filename
            if item.source_path:
                return item.source_path.stem + ".md"
            return f"{item.item_id}.md"

        # Other types: use source filename with .json extension
        if item.source_path:
            return item.source_path.stem + ".json"
        return f"{item.item_id}.json"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename.

        Args:
            name: Original name.

        Returns:
            Sanitized filename (without extension).
        """
        # Replace problematic characters
        for char in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
            name = name.replace(char, "_")
        # Limit length
        if len(name) > 100:
            name = name[:100]
        return name.strip()


class SessionLoader(BaseStage):
    """Load stage for session output.

    Writes processed items to session output folder.
    """

    def __init__(
        self,
        output_path: Path | None = None,
        steps: list[BaseStep] | None = None,
    ):
        """Initialize SessionLoader.

        Args:
            output_path: Override output path for session output.
            steps: Optional custom steps. Defaults to standard load steps.
        """
        super().__init__()
        self._output_path = output_path
        # Write to session folder
        self._steps = steps or [
            WriteToSessionStep(output_path),
        ]

    @property
    def stage_type(self) -> StageType:
        return StageType.LOAD

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps

    # T037: run_with_skip() method removed - Resume logic now in BaseStage.run()
