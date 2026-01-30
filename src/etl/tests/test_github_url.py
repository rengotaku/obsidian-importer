"""Unit tests for GitHub URL parsing and Jekyll frontmatter processing."""

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.utils.github_url import (
    GitHubRepoInfo,
    clone_repo,
    convert_frontmatter,
    extract_date,
    extract_date_from_text,
    extract_tags,
    parse_frontmatter,
    parse_github_url,
)


class TestParseGitHubUrl(unittest.TestCase):
    """Test parse_github_url() function."""

    def test_valid_url(self):
        """Test parsing valid GitHub URL."""
        url = "https://github.com/user/repo/tree/master/_posts"
        result = parse_github_url(url)

        self.assertIsNotNone(result)
        self.assertEqual(result.owner, "user")
        self.assertEqual(result.repo, "repo")
        self.assertEqual(result.branch, "master")
        self.assertEqual(result.path, "_posts")

    def test_url_with_nested_path(self):
        """Test URL with nested path."""
        url = "https://github.com/owner/repository/tree/main/docs/posts"
        result = parse_github_url(url)

        self.assertIsNotNone(result)
        self.assertEqual(result.path, "docs/posts")

    def test_invalid_url_format(self):
        """Test invalid URL returns None."""
        invalid_urls = [
            "https://github.com/user/repo",
            "https://gitlab.com/user/repo/tree/master/_posts",
            "not a url",
            "",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                result = parse_github_url(url)
                self.assertIsNone(result)

    def test_repo_info_properties(self):
        """Test GitHubRepoInfo derived properties."""
        url = "https://github.com/user/repo/tree/master/_posts"
        result = parse_github_url(url)

        self.assertEqual(result.clone_url, "https://github.com/user/repo.git")
        self.assertEqual(result.full_path, "repo/_posts")


class TestCloneRepo(unittest.TestCase):
    """Test clone_repo() function."""

    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    def test_clone_repo_success(self, mock_mkdtemp, mock_run):
        """Test successful repository cloning."""
        mock_mkdtemp.return_value = "/tmp/test_dir"
        mock_run.return_value = MagicMock(returncode=0)

        repo_info = GitHubRepoInfo(owner="user", repo="repo", branch="master", path="_posts")

        result = clone_repo(repo_info)

        # Verify git clone was called
        self.assertEqual(mock_run.call_count, 2)
        clone_call = mock_run.call_args_list[0]
        self.assertIn("git", clone_call[0][0])
        self.assertIn("clone", clone_call[0][0])
        self.assertIn("https://github.com/user/repo.git", clone_call[0][0])

        # Verify sparse-checkout was called
        sparse_call = mock_run.call_args_list[1]
        self.assertIn("sparse-checkout", sparse_call[0][0])
        self.assertIn("_posts", sparse_call[0][0])

        self.assertEqual(result, Path("/tmp/test_dir/repo/_posts"))


class TestParseFrontmatter(unittest.TestCase):
    """Test parse_frontmatter() function."""

    def test_valid_frontmatter(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
title: Test Post
tags:
  - tag1
  - tag2
---

Body content here."""

        fm, body = parse_frontmatter(content)

        self.assertEqual(fm["title"], "Test Post")
        self.assertEqual(fm["tags"], ["tag1", "tag2"])
        self.assertEqual(body, "\nBody content here.")

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "Just body content"
        fm, body = parse_frontmatter(content)

        self.assertEqual(fm, {})
        self.assertEqual(body, content)

    def test_invalid_yaml(self):
        """Test content with invalid YAML."""
        content = """---
invalid: yaml: structure: broken
---

Body"""
        fm, body = parse_frontmatter(content)

        self.assertEqual(fm, {})
        self.assertEqual(body, content)


class TestExtractDate(unittest.TestCase):
    """Test extract_date() and extract_date_from_text() functions."""

    def test_extract_from_frontmatter(self):
        """Test date extraction from frontmatter."""
        fm = {"date": "2024-09-10T15:30:00+09:00"}
        result = extract_date(fm, "test.md", "", "")
        self.assertEqual(result, "2024-09-10")

    def test_extract_from_filename(self):
        """Test date extraction from Jekyll filename."""
        fm = {}
        filename = "2024-09-10-post-title.md"
        result = extract_date(fm, filename, "", "")
        self.assertEqual(result, "2024-09-10")

    def test_extract_from_title(self):
        """Test date extraction from title."""
        fm = {}
        filename = "post.md"
        title = "Post from 2024/09/10"
        result = extract_date(fm, filename, title, "")
        self.assertEqual(result, "2024-09-10")

    def test_extract_from_body(self):
        """Test date extraction from body."""
        fm = {}
        filename = "post.md"
        title = "Title"
        body = "Written on 2024年9月10日\n\nContent..."
        result = extract_date(fm, filename, title, body)
        self.assertEqual(result, "2024-09-10")

    def test_fallback_current_date(self):
        """Test fallback to current date."""
        fm = {}
        filename = "post.md"
        title = "Title"
        body = "Content without date"

        result = extract_date(fm, filename, title, body)

        # Should be today's date
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(result, today)

    def test_date_patterns(self):
        """Test various date patterns."""
        test_cases = [
            ("2024-09-10", "2024-09-10"),
            ("2024/09/10", "2024-09-10"),
            ("2024年9月10日", "2024-09-10"),
            ("2024年9月5日", "2024-09-05"),  # Single digit day
        ]

        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = extract_date_from_text(input_text)
                self.assertEqual(result, expected)


class TestExtractTags(unittest.TestCase):
    """Test extract_tags() function."""

    def test_extract_from_frontmatter_tags(self):
        """Test tag extraction from frontmatter.tags."""
        fm = {"tags": ["react", "javascript"]}
        body = ""
        result = extract_tags(fm, body)
        self.assertIn("react", result)
        self.assertIn("javascript", result)

    def test_extract_from_categories(self):
        """Test tag extraction from categories."""
        fm = {"categories": ["programming", "web"]}
        body = ""
        result = extract_tags(fm, body)
        self.assertIn("programming", result)
        self.assertIn("web", result)

    def test_extract_from_keywords(self):
        """Test tag extraction from keywords."""
        fm = {"keywords": ["react", "ベジプロ", "プログラム"]}
        body = ""
        result = extract_tags(fm, body)
        self.assertIn("react", result)
        self.assertIn("ベジプロ", result)
        self.assertIn("プログラム", result)

    def test_extract_from_body_hashtags(self):
        """Test hashtag extraction from body."""
        fm = {}
        body = "Content with #aws and #kubernetes tags."
        result = extract_tags(fm, body)
        self.assertIn("aws", result)
        self.assertIn("kubernetes", result)

    def test_merge_and_deduplicate(self):
        """Test merging tags from multiple sources and deduplication."""
        fm = {
            "tags": ["react"],
            "categories": ["javascript"],
            "keywords": ["react", "programming"],
        }
        body = "Using #react for #programming"
        result = extract_tags(fm, body)

        # Should contain unique tags only
        self.assertIn("react", result)
        self.assertIn("javascript", result)
        self.assertIn("programming", result)
        # Count should be 3 (deduplicated)
        self.assertEqual(len(result), 3)

    def test_ignore_invalid_hashtags(self):
        """Test that invalid hashtags are ignored."""
        fm = {}
        body = "#123 ##heading #valid-tag #_invalid"
        result = extract_tags(fm, body)

        # Should only extract valid-tag
        self.assertIn("valid-tag", result)
        self.assertNotIn("123", result)
        self.assertNotIn("heading", result)


class TestConvertFrontmatter(unittest.TestCase):
    """Test convert_frontmatter() function."""

    def test_basic_conversion(self):
        """Test basic Jekyll to Obsidian conversion."""
        jekyll_fm = {
            "title": "Test Post",
            "date": "2024-09-10T15:30:00+09:00",
            "tags": ["react"],
        }
        filename = "2024-09-10-test.md"
        body = "Content"
        raw_content = "---\ntitle: Test\n---\nContent"

        result = convert_frontmatter(jekyll_fm, filename, body, raw_content)

        self.assertEqual(result["title"], "Test Post")
        self.assertEqual(result["created"], "2024-09-10")
        self.assertIn("react", result["tags"])
        self.assertTrue(result["normalized"])
        self.assertIn("file_id", result)
        self.assertEqual(len(result["file_id"]), 64)  # SHA256 hash length

    def test_title_fallback(self):
        """Test title fallback to filename."""
        jekyll_fm = {}
        filename = "2024-09-10-my-post.md"
        body = ""
        raw_content = "content"

        result = convert_frontmatter(jekyll_fm, filename, body, raw_content)

        self.assertEqual(result["title"], "my-post")

    def test_merge_tags_categories_keywords(self):
        """Test merging tags, categories, and keywords."""
        jekyll_fm = {
            "title": "Test",
            "tags": ["react"],
            "categories": ["web"],
            "keywords": ["programming"],
        }
        filename = "test.md"
        body = "Using #typescript"
        raw_content = "content"

        result = convert_frontmatter(jekyll_fm, filename, body, raw_content)

        tags = result["tags"]
        self.assertIn("react", tags)
        self.assertIn("web", tags)
        self.assertIn("programming", tags)
        self.assertIn("typescript", tags)

    def test_file_id_generation(self):
        """Test consistent file_id generation."""
        jekyll_fm = {"title": "Test"}
        filename = "test.md"
        body = "Content"
        raw_content = "same content"

        result1 = convert_frontmatter(jekyll_fm, filename, body, raw_content)
        result2 = convert_frontmatter(jekyll_fm, filename, body, raw_content)

        # Same content should produce same file_id
        self.assertEqual(result1["file_id"], result2["file_id"])

        # Different content should produce different file_id
        result3 = convert_frontmatter(jekyll_fm, filename, body, "different content")
        self.assertNotEqual(result1["file_id"], result3["file_id"])


if __name__ == "__main__":
    unittest.main()
