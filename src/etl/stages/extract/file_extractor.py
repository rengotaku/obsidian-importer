"""FileExtractor stage for ETL pipeline.

Extracts content from Markdown files.
"""

from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.types import StageType


class ReadMarkdownStep(BaseStep):
    """Read Markdown file content."""

    @property
    def name(self) -> str:
        return "read_markdown"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Read Markdown file content.

        Args:
            item: Item with source_path pointing to Markdown file.

        Returns:
            Item with content set to file contents.
        """
        content = item.source_path.read_text(encoding="utf-8")
        item.content = content
        item.metadata["source_type"] = "markdown"
        item.metadata["original_size"] = len(content)
        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input is a Markdown file."""
        return item.source_path.suffix.lower() == ".md"


class ParseFrontmatterStep(BaseStep):
    """Parse YAML frontmatter from Markdown."""

    @property
    def name(self) -> str:
        return "parse_frontmatter"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Parse YAML frontmatter from content.

        Args:
            item: Item with Markdown content.

        Returns:
            Item with frontmatter metadata extracted.
        """
        if item.content is None:
            return item

        content = item.content
        lines = content.split("\n")

        # Check for frontmatter delimiter
        if lines and lines[0].strip() == "---":
            # Find closing delimiter
            end_idx = None
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    end_idx = i
                    break

            if end_idx:
                frontmatter_lines = lines[1:end_idx]
                body_lines = lines[end_idx + 1 :]

                # Parse frontmatter (simple key: value parsing)
                frontmatter = {}
                for line in frontmatter_lines:
                    if ":" in line:
                        key, _, value = line.partition(":")
                        frontmatter[key.strip()] = value.strip()

                item.metadata["frontmatter"] = frontmatter
                item.metadata["has_frontmatter"] = True
                item.metadata["body_start_line"] = end_idx + 1
            else:
                item.metadata["has_frontmatter"] = False
        else:
            item.metadata["has_frontmatter"] = False

        return item


class FileExtractor(BaseStage):
    """Extract stage for Markdown files.

    Reads Markdown files and extracts content with frontmatter.
    """

    def __init__(self, steps: list[BaseStep] | None = None):
        """Initialize FileExtractor.

        Args:
            steps: Optional custom steps. Defaults to standard extraction steps.
        """
        super().__init__()
        self._steps = steps or [
            ReadMarkdownStep(),
            ParseFrontmatterStep(),
        ]

    @property
    def stage_type(self) -> StageType:
        return StageType.EXTRACT

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps
