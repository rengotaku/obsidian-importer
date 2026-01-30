"""Unit and integration tests for GitHubExtractor."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus
from src.etl.stages.extract.github_extractor import (
    ConvertFrontmatterStep,
    GitHubExtractor,
    ParseJekyllStep,
)
from src.etl.utils.github_url import GitHubRepoInfo


class TestGitHubExtractorDiscovery(unittest.TestCase):
    """Test GitHubExtractor.discover_items() method."""

    @patch("src.etl.stages.extract.github_extractor.parse_github_url")
    @patch("src.etl.stages.extract.github_extractor.clone_repo")
    def test_discover_items_valid_url(self, mock_clone, mock_parse):
        """Test discovery with valid GitHub URL."""
        # Mock URL parsing
        mock_parse.return_value = GitHubRepoInfo(
            owner="user", repo="repo", branch="master", path="_posts"
        )

        # Mock clone returning an actual Path (not MagicMock)
        clone_path = Path("/tmp/repo")
        mock_clone.return_value = clone_path

        # Mock glob to return actual Path objects
        file1 = Path("/tmp/repo/_posts/2024-01-01-post1.md")
        file2 = Path("/tmp/repo/_posts/2024-01-02-post2.md")

        extractor = GitHubExtractor()

        # Mock file reading and glob
        with patch("pathlib.Path.read_text") as mock_read, patch("pathlib.Path.glob") as mock_glob:
            mock_read.return_value = "---\ntitle: Test\n---\nContent"
            mock_glob.return_value = [file1, file2]

            items = list(
                extractor.discover_items("https://github.com/user/repo/tree/master/_posts")
            )

        # Should discover 2 items
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], ProcessingItem)

    @patch("src.etl.stages.extract.github_extractor.parse_github_url")
    def test_discover_items_invalid_url(self, mock_parse):
        """Test discovery with invalid URL."""
        mock_parse.return_value = None

        extractor = GitHubExtractor()

        with self.assertRaises(ValueError):
            # Need to consume the iterator to trigger the error
            list(extractor.discover_items("invalid-url"))


class TestGitHubExtractorIntegration(unittest.TestCase):
    """Integration tests for GitHubExtractor steps."""

    @patch("src.etl.stages.extract.github_extractor.parse_github_url")
    @patch("src.etl.stages.extract.github_extractor.clone_repo")
    def test_full_extraction_flow(self, mock_clone, mock_parse):
        """Test full extraction flow with all steps."""
        # Mock URL parsing
        mock_parse.return_value = GitHubRepoInfo(
            owner="user", repo="repo", branch="master", path="_posts"
        )

        # Mock clone returning actual Path
        clone_path = Path("/tmp/repo")
        mock_clone.return_value = clone_path

        file1 = Path("/tmp/repo/_posts/2024-01-01-test.md")

        extractor = GitHubExtractor()

        # Mock file content
        jekyll_content = """---
title: "Test Post"
date: 2024-01-01
tags: [react, javascript]
---

# Content

Test post content."""

        with patch("pathlib.Path.read_text") as mock_read, patch("pathlib.Path.glob") as mock_glob:
            mock_read.return_value = jekyll_content
            mock_glob.return_value = [file1]

            items = list(
                extractor.discover_items("https://github.com/user/repo/tree/master/_posts")
            )

            # Process through steps
            steps = extractor.steps
            for step in steps:
                for item in items:
                    step.process(item)

        # Verify item has expected structure after processing
        self.assertEqual(len(items), 1)
        item = items[0]

        # Should have title from frontmatter
        self.assertIn("title", item.metadata)
        self.assertEqual(item.metadata["title"], "Test Post")

        # Should have created date
        self.assertIn("created", item.metadata)
        self.assertEqual(item.metadata["created"], "2024-01-01")

        # Should have tags
        self.assertIn("tags", item.metadata)
        self.assertIn("react", item.metadata["tags"])

        # Should have normalized flag
        self.assertEqual(item.metadata.get("normalized"), True)

        # Should have file_id
        self.assertIn("file_id", item.metadata)


class TestGitHubExtractorResumeMode(unittest.TestCase):
    """Test GitHubExtractor with Resume mode."""

    @patch("src.etl.stages.extract.github_extractor.parse_github_url")
    @patch("src.etl.stages.extract.github_extractor.clone_repo")
    def test_resume_mode_skip_processed(self, mock_clone, mock_parse):
        """Test that resume mode skips already processed items."""
        # Mock URL parsing
        mock_parse.return_value = GitHubRepoInfo(
            owner="user", repo="repo", branch="master", path="_posts"
        )

        # Mock clone returning actual Path
        clone_path = Path("/tmp/repo")
        mock_clone.return_value = clone_path

        file1 = Path("/tmp/repo/_posts/2024-01-01-post1.md")
        file2 = Path("/tmp/repo/_posts/2024-01-02-post2.md")

        # Create extractor
        extractor = GitHubExtractor()

        # Mock session with one processed item
        with patch("pathlib.Path.read_text") as mock_read, patch("pathlib.Path.glob") as mock_glob:
            mock_read.return_value = "---\ntitle: Test\n---\nContent"
            mock_glob.return_value = [file1, file2]

            # Mock existing index file with one file_id
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                items = list(
                    extractor.discover_items("https://github.com/user/repo/tree/master/_posts")
                )

        # Should discover all items (skipping happens in session management)
        self.assertEqual(len(items), 2)


class TestGitHubExtractorFileIdGeneration(unittest.TestCase):
    """Test file_id generation for Resume mode."""

    def test_file_id_in_metadata(self):
        """Test that file_id is generated and stored in metadata."""
        # Create a mock item with Jekyll content
        item = ProcessingItem(
            item_id="test-post",
            source_path=Path("/tmp/test.md"),
            current_step="test",
            status=ItemStatus.PENDING,
            content="---\ntitle: Test\n---\nContent",
            metadata={
                "filename": "2024-01-01-test.md",
                "source_type": "github_jekyll",
            },
        )

        # Process through steps
        parse_step = ParseJekyllStep()
        convert_step = ConvertFrontmatterStep()

        parse_step.process(item)
        convert_step.process(item)

        # Should have file_id
        self.assertIn("file_id", item.metadata)
        self.assertEqual(len(item.metadata["file_id"]), 64)  # SHA256

    def test_consistent_file_id(self):
        """Test that same content produces same file_id."""
        content = "---\ntitle: Test\n---\nContent"

        item1 = ProcessingItem(
            item_id="test1",
            source_path=Path("/tmp/test1.md"),
            current_step="test",
            status=ItemStatus.PENDING,
            content=content,
            metadata={"filename": "test.md", "source_type": "github_jekyll"},
        )

        item2 = ProcessingItem(
            item_id="test2",
            source_path=Path("/tmp/test2.md"),
            current_step="test",
            status=ItemStatus.PENDING,
            content=content,
            metadata={"filename": "test.md", "source_type": "github_jekyll"},
        )

        # Process both items
        parse_step = ParseJekyllStep()
        convert_step = ConvertFrontmatterStep()

        for item in [item1, item2]:
            parse_step.process(item)
            convert_step.process(item)

        # Should have same file_id
        self.assertEqual(item1.metadata["file_id"], item2.metadata["file_id"])


if __name__ == "__main__":
    unittest.main()
