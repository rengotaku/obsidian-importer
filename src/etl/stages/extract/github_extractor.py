"""GitHub/Jekyll blog extractor for ETL pipeline.

Extracts Jekyll blog posts from GitHub repositories and converts them to
Obsidian format.
"""

import logging
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

from src.etl.core.extractor import BaseExtractor
from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStep
from src.etl.core.status import ItemStatus
from src.etl.utils.github_url import (
    clone_repo,
    convert_frontmatter,
    parse_frontmatter,
    parse_github_url,
)

logger = logging.getLogger(__name__)


class CloneRepoStep(BaseStep):
    """Step to clone GitHub repository."""

    def __init__(self):
        """Initialize CloneRepoStep."""
        self._temp_dir = None

    @property
    def name(self) -> str:
        return "clone_repo"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Clone repository and store path in metadata.

        Args:
            item: Item with github_url in metadata

        Returns:
            Item with clone_path in metadata
        """
        github_url = item.metadata.get("github_url")
        if not github_url:
            item.metadata["clone_error"] = "Missing github_url"
            return item

        repo_info = parse_github_url(github_url)
        if not repo_info:
            item.metadata["clone_error"] = "Invalid GitHub URL"
            return item

        try:
            # Create temp directory for this clone operation
            if not self._temp_dir:
                self._temp_dir = Path(tempfile.mkdtemp(prefix="github_clone_"))

            clone_path = clone_repo(repo_info, self._temp_dir)
            item.metadata["clone_path"] = str(clone_path)
            item.metadata["repo_info"] = {
                "owner": repo_info.owner,
                "repo": repo_info.repo,
                "branch": repo_info.branch,
                "path": repo_info.path,
            }
        except Exception as e:
            item.metadata["clone_error"] = str(e)
            logger.error(f"Failed to clone repository: {e}")

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has github_url."""
        return "github_url" in item.metadata

    def __del__(self):
        """Cleanup temp directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)


class ParseJekyllStep(BaseStep):
    """Parse Jekyll frontmatter and body."""

    @property
    def name(self) -> str:
        return "parse_jekyll"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Parse Jekyll frontmatter from content.

        Args:
            item: Item with content set to raw Markdown

        Returns:
            Item with parsed frontmatter in metadata
        """
        if not item.content:
            return item

        try:
            frontmatter, body = parse_frontmatter(item.content)
            item.metadata["jekyll_frontmatter"] = frontmatter
            item.metadata["body"] = body

            # Skip draft or private posts
            if frontmatter.get("draft") is True:
                item.metadata["skip_reason"] = "draft=true"
            elif frontmatter.get("private") is True:
                item.metadata["skip_reason"] = "private=true"

        except Exception as e:
            item.metadata["parse_error"] = str(e)
            logger.warning(f"Failed to parse frontmatter for {item.item_id}: {e}")

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has content."""
        return item.content is not None


class ConvertFrontmatterStep(BaseStep):
    """Convert Jekyll frontmatter to Obsidian format."""

    @property
    def name(self) -> str:
        return "convert_frontmatter"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Convert Jekyll frontmatter to Obsidian format.

        Args:
            item: Item with jekyll_frontmatter in metadata

        Returns:
            Item with obsidian_frontmatter in metadata
        """
        if item.metadata.get("skip_reason"):
            return item

        jekyll_fm = item.metadata.get("jekyll_frontmatter", {})
        body = item.metadata.get("body", "")
        filename = item.metadata.get("filename", item.item_id)
        raw_content = item.content or ""

        try:
            obsidian_fm = convert_frontmatter(jekyll_fm, filename, body, raw_content)
            item.metadata["obsidian_frontmatter"] = obsidian_fm

            # Update item metadata with converted fields
            item.metadata["title"] = obsidian_fm.get("title", "")
            item.metadata["created"] = obsidian_fm.get("created", "")
            item.metadata["tags"] = obsidian_fm.get("tags", [])
            item.metadata["normalized"] = obsidian_fm.get("normalized", True)
            item.metadata["file_id"] = obsidian_fm.get("file_id", "")

            # Generate Obsidian Markdown content (frontmatter + body)
            import yaml

            frontmatter_yaml = yaml.dump(
                obsidian_fm, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            item.content = f"---\n{frontmatter_yaml}---\n\n{body}"

        except Exception as e:
            item.metadata["conversion_error"] = str(e)
            logger.warning(f"Failed to convert frontmatter for {item.item_id}: {e}")

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has jekyll_frontmatter."""
        return "jekyll_frontmatter" in item.metadata


class GitHubExtractor(BaseExtractor):
    """Extract Jekyll blog posts from GitHub repository."""

    def __init__(self):
        """Initialize GitHub extractor."""
        super().__init__()
        self._temp_dir = None

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover items from GitHub URL (Phase 5 implementation).

        Args:
            input_path: Path to directory containing url.txt (or github_url.txt for backward compat),
                        or a string URL passed as Path-like

        Yields:
            ProcessingItem for each discovered Markdown file
        """
        # Handle both Path objects and string URLs (passed through Path interface)
        # When BaseExtractor calls this with discover_items(url_string), Python doesn't enforce
        # the Path type, so we get a string. We need to handle both cases.
        input_str = str(input_path)

        # Check if it's a URL
        if input_str.startswith("http://") or input_str.startswith("https://"):
            github_url = input_str
        elif isinstance(input_path, Path) and input_path.is_dir():
            # Directory containing url.txt or github_url.txt (backward compatibility)
            url_file = input_path / "url.txt"
            old_url_file = input_path / "github_url.txt"

            if url_file.exists():
                # New format: url.txt (may contain multiple URLs, take first line)
                github_url = url_file.read_text(encoding="utf-8").strip().split("\n")[0]
            elif old_url_file.exists():
                # Old format: github_url.txt
                github_url = old_url_file.read_text(encoding="utf-8").strip()
            else:
                raise ValueError(f"URL file not found: {url_file} or {old_url_file}")
        else:
            # Treat as URL string
            github_url = input_str

        # Parse GitHub URL
        repo_info = parse_github_url(github_url)
        if not repo_info:
            raise ValueError(f"Invalid GitHub URL: {github_url}")

        # Clone repository
        try:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="github_clone_"))
            clone_path = clone_repo(repo_info, self._temp_dir)
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {e}") from e

        # Discover and yield Markdown files
        md_files = list(clone_path.glob("**/*.md"))

        if not md_files:
            logger.warning(f"No Markdown files found in {clone_path}")
            return

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8")

                yield ProcessingItem(
                    item_id=md_file.stem,
                    source_path=md_file,
                    current_step="discover",
                    status=ItemStatus.PENDING,
                    content=content,
                    metadata={
                        "source_type": "github_jekyll",
                        "github_url": github_url,
                        "filename": md_file.name,
                        "relative_path": str(md_file.relative_to(clone_path)),
                    },
                )

            except Exception as e:
                logger.error(f"Failed to read {md_file}: {e}")
                continue

        logger.info(f"Discovered {len(md_files)} Markdown files from {repo_info.full_path}")

    def _build_conversation_for_chunking(self, item: ProcessingItem):
        """GitHub articles don't need chunking (Phase 5 implementation).

        Returns:
            None to signal BaseExtractor to skip chunking
        """
        # GitHub articles are individual blog posts, not conversations
        # They don't need chunking like Claude/ChatGPT conversations
        return None

    @property
    def steps(self) -> list[BaseStep]:
        """Return processing steps for GitHub extraction.

        Returns:
            List of steps to execute
        """
        return [
            ParseJekyllStep(),
            ConvertFrontmatterStep(),
        ]

    def __del__(self):
        """Cleanup temp directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
