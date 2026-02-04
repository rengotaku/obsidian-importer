"""Tests for GitHub Jekyll Extract pipeline nodes.

Phase 8 RED tests: clone_github_repo, parse_jekyll, convert_frontmatter nodes.
These tests verify:
- clone_github_repo: URL -> sparse-checkout -> local Markdown files (subprocess mocked)
- parse_jekyll: Markdown + YAML frontmatter -> ParsedItem dict
- parse_jekyll skip: draft: true / private: true -> excluded from output
- convert_frontmatter: Jekyll frontmatter -> Obsidian format (date->created, tags/categories/keywords->tags)
- Date extraction priority: frontmatter.date -> filename -> regex -> current datetime
- Idempotent existing_output parameter (backward compat, ignored)
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from obsidian_etl.pipelines.extract_github.nodes import (
    clone_github_repo,
    convert_frontmatter,
    parse_jekyll,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


def _read_fixture(name: str) -> str:
    """Read a fixture file and return its content as string."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _make_jekyll_post(
    filename: str = "2022-10-17-Online-DDL-of-mysql.md",
    title: str = "Online DDL of MySQL",
    date: str = "2022-10-17",
    tags: list[str] | None = None,
    categories: list[str] | None = None,
    keywords: list[str] | None = None,
    draft: bool | None = None,
    private: bool | None = None,
    body: str = "## Introduction\n\nOnline DDL in MySQL is powerful.",
    extra_frontmatter: dict | None = None,
) -> str:
    """Build a Jekyll Markdown post with YAML frontmatter.

    Args:
        filename: Jekyll-style filename (not used in content, for reference).
        title: Post title.
        date: Date string (YYYY-MM-DD).
        tags: Tag list.
        categories: Category list.
        keywords: Keyword list.
        draft: If True, marks post as draft.
        private: If True, marks post as private.
        body: Post body content.
        extra_frontmatter: Additional frontmatter fields.

    Returns:
        Complete Markdown string with YAML frontmatter.
    """
    fm_lines = []
    fm_lines.append(f"title: {title}")
    if date is not None:
        fm_lines.append(f"date: {date}")
    if tags is not None:
        fm_lines.append("tags:")
        for tag in tags:
            fm_lines.append(f"  - {tag}")
    if categories is not None:
        fm_lines.append("categories:")
        for cat in categories:
            fm_lines.append(f"  - {cat}")
    if keywords is not None:
        fm_lines.append("keywords:")
        for kw in keywords:
            fm_lines.append(f"  - {kw}")
    if draft is not None:
        fm_lines.append(f"draft: {'true' if draft else 'false'}")
    if private is not None:
        fm_lines.append(f"private: {'true' if private else 'false'}")
    if extra_frontmatter:
        for key, val in extra_frontmatter.items():
            fm_lines.append(f"{key}: {val}")

    frontmatter = "\n".join(fm_lines)
    return f"---\n{frontmatter}\n---\n\n{body}"


def _make_partitioned_input(file_map: dict[str, str]) -> dict[str, callable]:
    """Create a Kedro PartitionedDataset-style input dict.

    Each key is a filename, value is a callable returning Markdown text.

    Args:
        file_map: Dict of filename -> Markdown content string.

    Returns:
        Dict of filename -> callable returning string.
    """
    return {name: (lambda content=text: content) for name, text in file_map.items()}


# ---------------------------------------------------------------------------
# TestCloneGithubRepo: URL -> sparse-checkout -> local files (mock subprocess)
# ---------------------------------------------------------------------------


class TestCloneGithubRepo(unittest.TestCase):
    """clone_github_repo: GitHub URL -> sparse-checkout -> local Markdown files."""

    @patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")
    def test_clone_returns_dict_of_markdown_files(self, mock_subprocess):
        """clone_github_repo が dict[str, Callable] を返すこと。

        subprocess.run をモックし、一時ディレクトリに Markdown ファイルを配置。
        """
        import os
        import tempfile

        # Create temp dir with sample Markdown files
        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir) / "repo" / "_posts"
            posts_dir.mkdir(parents=True)

            # Create sample files
            post1 = posts_dir / "2022-10-17-Online-DDL-of-mysql.md"
            post1.write_text(_make_jekyll_post(), encoding="utf-8")

            post2 = posts_dir / "2023-01-05-Docker-networking.md"
            post2.write_text(
                _make_jekyll_post(
                    title="Docker networking",
                    date="2023-01-05",
                    body="## Docker\n\nNetworking in Docker containers.",
                ),
                encoding="utf-8",
            )

            # Mock subprocess.run to not actually run git
            mock_subprocess.run.return_value = MagicMock(returncode=0)

            url = "https://github.com/testuser/testblog/tree/master/_posts"
            params = {"github_clone_dir": tmpdir}

            result = clone_github_repo(url, params)

            self.assertIsInstance(result, dict)
            self.assertGreater(len(result), 0)

    @patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")
    def test_clone_calls_git_with_depth_1(self, mock_subprocess):
        """git clone が --depth 1 で呼び出されること。"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir) / "repo" / "_posts"
            posts_dir.mkdir(parents=True)
            (posts_dir / "test.md").write_text(_make_jekyll_post(), encoding="utf-8")

            mock_subprocess.run.return_value = MagicMock(returncode=0)

            url = "https://github.com/testuser/testblog/tree/master/_posts"
            params = {"github_clone_dir": tmpdir}

            clone_github_repo(url, params)

            # Verify git clone was called with --depth 1
            calls = mock_subprocess.run.call_args_list
            clone_call_args = None
            for call in calls:
                args = call[0][0] if call[0] else call[1].get("args", [])
                if isinstance(args, list) and "clone" in args:
                    clone_call_args = args
                    break

            self.assertIsNotNone(clone_call_args)
            self.assertIn("--depth", clone_call_args)
            depth_idx = clone_call_args.index("--depth")
            self.assertEqual(clone_call_args[depth_idx + 1], "1")

    @patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")
    def test_clone_calls_sparse_checkout(self, mock_subprocess):
        """git sparse-checkout set が呼び出されること。"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir) / "repo" / "_posts"
            posts_dir.mkdir(parents=True)
            (posts_dir / "test.md").write_text(_make_jekyll_post(), encoding="utf-8")

            mock_subprocess.run.return_value = MagicMock(returncode=0)

            url = "https://github.com/testuser/testblog/tree/master/_posts"
            params = {"github_clone_dir": tmpdir}

            clone_github_repo(url, params)

            # Check sparse-checkout was called
            calls = mock_subprocess.run.call_args_list
            sparse_call_found = False
            for call in calls:
                args = call[0][0] if call[0] else call[1].get("args", [])
                if isinstance(args, list) and "sparse-checkout" in args:
                    sparse_call_found = True
                    break

            self.assertTrue(sparse_call_found)

    @patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")
    def test_clone_invalid_url_returns_empty(self, mock_subprocess):
        """無効な URL が空 dict を返すこと。"""
        result = clone_github_repo("not-a-github-url", {})
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    @patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")
    def test_clone_result_values_are_callable(self, mock_subprocess):
        """返り値の各値が callable であること（PartitionedDataset パターン）。"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir) / "repo" / "_posts"
            posts_dir.mkdir(parents=True)
            (posts_dir / "test.md").write_text(_make_jekyll_post(), encoding="utf-8")

            mock_subprocess.run.return_value = MagicMock(returncode=0)

            url = "https://github.com/testuser/testblog/tree/master/_posts"
            params = {"github_clone_dir": tmpdir}

            result = clone_github_repo(url, params)

            for key, loader in result.items():
                self.assertTrue(callable(loader))
                content = loader()
                self.assertIsInstance(content, str)
                self.assertGreater(len(content), 0)


# ---------------------------------------------------------------------------
# TestParseJekyll: Markdown + frontmatter -> ParsedItem dict
# ---------------------------------------------------------------------------


class TestParseJekyll(unittest.TestCase):
    """parse_jekyll: Markdown files -> ParsedItem dict."""

    def setUp(self):
        """Create valid partitioned input with Jekyll posts."""
        post1 = _make_jekyll_post(
            title="Online DDL of MySQL",
            date="2022-10-17",
            tags=["mysql", "database"],
            body="## Introduction\n\nOnline DDL in MySQL is powerful.\n\nIt allows schema changes without downtime.",
        )
        post2 = _make_jekyll_post(
            title="Docker Networking Guide",
            date="2023-01-05",
            tags=["docker", "networking"],
            body="## Docker\n\nNetworking in Docker containers is flexible.",
        )

        self.partitioned_input = _make_partitioned_input(
            {
                "2022-10-17-Online-DDL-of-mysql.md": post1,
                "2023-01-05-Docker-networking.md": post2,
            }
        )

        # Load expected output reference
        with open(
            FIXTURES_DIR / "expected_outputs" / "parsed_github_item.json",
            encoding="utf-8",
        ) as f:
            self.expected_item = json.load(f)

    def test_parse_jekyll_returns_dict(self):
        """parse_jekyll が dict を返すこと。"""
        result = parse_jekyll(self.partitioned_input)
        self.assertIsInstance(result, dict)

    def test_parse_jekyll_item_count(self):
        """2 ファイルから 2 ParsedItem が生成されること。"""
        result = parse_jekyll(self.partitioned_input)
        self.assertEqual(len(result), 2)

    def test_parse_jekyll_parsed_item_structure(self):
        """ParsedItem が E-2 スキーマに準拠すること（provider=github）。"""
        result = parse_jekyll(self.partitioned_input)

        first_item = list(result.values())[0]

        # Required fields from E-2 data model
        self.assertIn("item_id", first_item)
        self.assertEqual(first_item["source_provider"], "github")
        self.assertIn("source_path", first_item)
        self.assertIn("conversation_name", first_item)
        self.assertIn("created_at", first_item)
        self.assertIsInstance(first_item["messages"], list)
        self.assertIsInstance(first_item["content"], str)
        self.assertGreater(len(first_item["content"]), 10)
        self.assertIn("file_id", first_item)
        self.assertEqual(len(first_item["file_id"]), 12)
        self.assertFalse(first_item["is_chunked"])
        self.assertIsNone(first_item["chunk_index"])
        self.assertIsNone(first_item["total_chunks"])
        self.assertIsNone(first_item["parent_item_id"])

    def test_parse_jekyll_title_extracted(self):
        """frontmatter title が conversation_name に設定されること。"""
        result = parse_jekyll(self.partitioned_input)

        names = {item["conversation_name"] for item in result.values()}
        self.assertIn("Online DDL of MySQL", names)
        self.assertIn("Docker Networking Guide", names)

    def test_parse_jekyll_date_extracted(self):
        """frontmatter date が created_at に設定されること。"""
        result = parse_jekyll(self.partitioned_input)

        items = list(result.values())
        dates = {item["created_at"] for item in items}
        self.assertIn("2022-10-17", dates)
        self.assertIn("2023-01-05", dates)

    def test_parse_jekyll_content_is_body(self):
        """content がフロントマター除去後の本文であること。"""
        result = parse_jekyll(self.partitioned_input)

        first_item = list(result.values())[0]
        content = first_item["content"]

        # Content should contain the body, not frontmatter
        self.assertNotIn("---", content[:10])
        # Should contain actual body text
        self.assertTrue("Introduction" in content or "Docker" in content)

    def test_parse_jekyll_messages_empty_for_github(self):
        """GitHub プロバイダーでは messages が空リストであること。

        GitHub Jekyll ブログは会話ではないため、messages は空。
        content に本文全体が入る。
        """
        result = parse_jekyll(self.partitioned_input)

        first_item = list(result.values())[0]
        self.assertEqual(first_item["messages"], [])

    def test_parse_jekyll_file_id_valid_hex(self):
        """file_id が 12 桁の16進数文字列であること。"""
        result = parse_jekyll(self.partitioned_input)

        first_item = list(result.values())[0]
        file_id = first_item["file_id"]

        self.assertEqual(len(file_id), 12)
        int(file_id, 16)  # Raises ValueError if not valid hex

    def test_parse_jekyll_golden_data_match(self):
        """期待出力（ゴールデンデータ）との部分一致を確認。"""
        result = parse_jekyll(self.partitioned_input)

        # Find the item matching the expected title
        matching_items = [
            item
            for item in result.values()
            if item["conversation_name"] == self.expected_item["_expected_title"]
        ]
        self.assertEqual(len(matching_items), 1)

        item = matching_items[0]
        self.assertEqual(item["source_provider"], "github")
        self.assertEqual(item["created_at"], self.expected_item["_expected_created"])
        self.assertFalse(item["is_chunked"])

    def test_parse_jekyll_no_frontmatter_in_content(self):
        """content に YAML frontmatter が含まれないこと。"""
        result = parse_jekyll(self.partitioned_input)

        for item in result.values():
            # Content should not start with "---"
            self.assertFalse(item["content"].strip().startswith("---"))


# ---------------------------------------------------------------------------
# TestParseJekyllSkipDraft: draft: true / private: true -> excluded
# ---------------------------------------------------------------------------


class TestParseJekyllSkipDraft(unittest.TestCase):
    """parse_jekyll: draft/private posts are excluded."""

    def test_draft_true_excluded(self):
        """draft: true のファイルが出力から除外されること。"""
        draft_post = _make_jekyll_post(
            title="Draft Post",
            date="2023-06-01",
            draft=True,
            body="This is a draft post.",
        )
        normal_post = _make_jekyll_post(
            title="Published Post",
            date="2023-06-02",
            body="This is a published post with enough content.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-06-01-draft-post.md": draft_post,
                "2023-06-02-published-post.md": normal_post,
            }
        )

        result = parse_jekyll(partitioned)

        # Only the non-draft post should be in the output
        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertEqual(item["conversation_name"], "Published Post")

    def test_private_true_excluded(self):
        """private: true のファイルが出力から除外されること。"""
        private_post = _make_jekyll_post(
            title="Private Post",
            date="2023-07-01",
            private=True,
            body="This is a private post.",
        )
        normal_post = _make_jekyll_post(
            title="Public Post",
            date="2023-07-02",
            body="This is a public post with sufficient content.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-07-01-private-post.md": private_post,
                "2023-07-02-public-post.md": normal_post,
            }
        )

        result = parse_jekyll(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertEqual(item["conversation_name"], "Public Post")

    def test_draft_false_included(self):
        """draft: false のファイルは除外されないこと。"""
        post = _make_jekyll_post(
            title="Not a Draft",
            date="2023-08-01",
            draft=False,
            body="This post has draft set to false, so it should be included.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-08-01-not-draft.md": post,
            }
        )

        result = parse_jekyll(partitioned)
        self.assertEqual(len(result), 1)

    def test_all_drafts_returns_empty(self):
        """全ファイルが draft の場合、空 dict を返すこと。"""
        draft1 = _make_jekyll_post(
            title="Draft 1", date="2023-09-01", draft=True, body="Draft content."
        )
        draft2 = _make_jekyll_post(
            title="Draft 2", date="2023-09-02", draft=True, body="Another draft."
        )

        partitioned = _make_partitioned_input(
            {
                "2023-09-01-draft-1.md": draft1,
                "2023-09-02-draft-2.md": draft2,
            }
        )

        result = parse_jekyll(partitioned)
        self.assertEqual(len(result), 0)


# ---------------------------------------------------------------------------
# TestConvertFrontmatter: Jekyll -> Obsidian format conversion
# ---------------------------------------------------------------------------


class TestConvertFrontmatter(unittest.TestCase):
    """convert_frontmatter: Jekyll frontmatter -> Obsidian format."""

    def test_date_becomes_created(self):
        """Jekyll date フィールドが created に変換されること。"""
        post = _make_jekyll_post(
            title="Date Test",
            date="2022-10-17",
            body="Date conversion test body content.",
        )

        partitioned = _make_partitioned_input(
            {
                "2022-10-17-date-test.md": post,
            }
        )

        result = convert_frontmatter(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertEqual(item["created_at"], "2022-10-17")

    def test_tags_categories_keywords_merged(self):
        """tags, categories, keywords が統合されること。"""
        post = _make_jekyll_post(
            title="Tag Merge Test",
            date="2023-01-01",
            tags=["python", "web"],
            categories=["engineering"],
            keywords=["backend", "api"],
            body="Tag merging test content.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-01-01-tag-merge.md": post,
            }
        )

        result = convert_frontmatter(partitioned)

        item = list(result.values())[0]
        # The item should have merged tags from all sources
        # Access through metadata or a tags field
        self.assertIn("tags", item)
        tags = item["tags"]
        self.assertIn("python", tags)
        self.assertIn("web", tags)
        self.assertIn("engineering", tags)
        self.assertIn("backend", tags)
        self.assertIn("api", tags)

    def test_removed_fields_not_in_output(self):
        """Jekyll 固有フィールド (layout, permalink, slug, lastmod) が出力に含まれないこと。"""
        post = _make_jekyll_post(
            title="Field Removal Test",
            date="2023-02-01",
            body="Content for field removal test.",
            extra_frontmatter={
                "layout": "post",
                "permalink": "/2023/02/test/",
                "slug": "test-slug",
                "lastmod": "2023-03-01",
            },
        )

        partitioned = _make_partitioned_input(
            {
                "2023-02-01-field-removal.md": post,
            }
        )

        result = convert_frontmatter(partitioned)

        item = list(result.values())[0]
        # These Jekyll-specific fields should not be in the output metadata
        content = item.get("markdown_content", item.get("content", ""))
        self.assertNotIn("layout:", content[:500])
        self.assertNotIn("permalink:", content[:500])
        self.assertNotIn("slug:", content[:500])
        self.assertNotIn("lastmod:", content[:500])

    def test_normalized_true_in_output(self):
        """normalized: true が出力に含まれること。"""
        post = _make_jekyll_post(
            title="Normalized Test",
            date="2023-03-01",
            body="Content for normalized flag test.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-03-01-normalized.md": post,
            }
        )

        result = convert_frontmatter(partitioned)

        item = list(result.values())[0]
        # Check that normalized is set (in metadata or markdown_content)
        content = item.get("markdown_content", item.get("content", ""))
        self.assertIn("normalized", content)

    def test_file_id_generated(self):
        """file_id が SHA256 ハッシュから生成されること。"""
        post = _make_jekyll_post(
            title="FileID Test",
            date="2023-04-01",
            body="Content for file ID generation test.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-04-01-file-id.md": post,
            }
        )

        result = convert_frontmatter(partitioned)

        item = list(result.values())[0]
        self.assertIn("file_id", item)
        file_id = item["file_id"]
        self.assertIsInstance(file_id, str)
        self.assertGreater(len(file_id), 0)

    def test_title_fallback_to_filename(self):
        """title が frontmatter にない場合、ファイル名からフォールバックすること。"""
        # Post without title in frontmatter
        body = "Content without explicit title in frontmatter."
        content = f"---\ndate: 2023-05-01\n---\n\n{body}"

        partitioned = _make_partitioned_input(
            {
                "2023-05-01-my-article-title.md": content,
            }
        )

        result = convert_frontmatter(partitioned)

        item = list(result.values())[0]
        # Should derive title from filename (strip date prefix and .md)
        self.assertIn("conversation_name", item)
        self.assertIsNotNone(item["conversation_name"])
        self.assertGreater(len(item["conversation_name"]), 0)


# ---------------------------------------------------------------------------
# TestDateExtractionPriority: frontmatter.date -> filename -> regex -> current
# ---------------------------------------------------------------------------


class TestDateExtractionPriority(unittest.TestCase):
    """Date extraction priority: frontmatter.date -> filename -> regex -> current datetime."""

    def test_priority_1_frontmatter_date(self):
        """最優先: frontmatter.date が使用されること。"""
        post = _make_jekyll_post(
            title="Frontmatter Date",
            date="2022-06-15",
            body="Body with a date 2020-01-01 that should be ignored.",
        )

        partitioned = _make_partitioned_input(
            {
                "2021-03-20-different-filename-date.md": post,
            }
        )

        result = parse_jekyll(partitioned)

        item = list(result.values())[0]
        # Frontmatter date should take priority over filename date
        self.assertEqual(item["created_at"], "2022-06-15")

    def test_priority_2_filename_date(self):
        """第2優先: ファイル名の日付が使用されること（frontmatter.date なし）。"""
        body = "Body content without date references."
        content = f"---\ntitle: Filename Date Test\n---\n\n{body}"

        partitioned = _make_partitioned_input(
            {
                "2021-11-25-filename-date-test.md": content,
            }
        )

        result = parse_jekyll(partitioned)

        item = list(result.values())[0]
        self.assertEqual(item["created_at"], "2021-11-25")

    def test_priority_3_body_regex(self):
        """第3優先: 本文の正規表現から日付抽出されること。"""
        body = "This post was written on 2020-08-10 about testing."
        content = f"---\ntitle: Regex Date Test\n---\n\n{body}"

        partitioned = _make_partitioned_input(
            {
                "no-date-in-filename.md": content,
            }
        )

        result = parse_jekyll(partitioned)

        item = list(result.values())[0]
        self.assertEqual(item["created_at"], "2020-08-10")

    def test_priority_4_current_datetime_fallback(self):
        """最低優先: 日付情報がない場合、現在日時にフォールバックすること。"""
        body = "No date anywhere in this content."
        content = f"---\ntitle: No Date Test\n---\n\n{body}"

        partitioned = _make_partitioned_input(
            {
                "no-date-at-all.md": content,
            }
        )

        result = parse_jekyll(partitioned)

        item = list(result.values())[0]
        # Should have a non-None created_at (fallback to current date)
        self.assertIsNotNone(item["created_at"])
        # Should be in YYYY-MM-DD format
        self.assertRegex(item["created_at"], r"^\d{4}-\d{2}-\d{2}")

    def test_iso8601_date_in_frontmatter(self):
        """frontmatter.date が ISO 8601 形式の場合、YYYY-MM-DD に変換されること。"""
        body = "ISO date format test."
        content = "---\ntitle: ISO Date\ndate: 2022-10-17T12:30:00+09:00\n---\n\n" + body

        partitioned = _make_partitioned_input(
            {
                "iso-date-test.md": content,
            }
        )

        result = parse_jekyll(partitioned)

        item = list(result.values())[0]
        # Should extract just the date portion
        self.assertTrue(item["created_at"].startswith("2022-10-17"))


# ---------------------------------------------------------------------------
# TestIdempotentExtractGithub: existing_output parameter (backward compat)
# ---------------------------------------------------------------------------


class TestIdempotentExtractGithub(unittest.TestCase):
    """parse_jekyll / convert_frontmatter: existing_output parameter."""

    def _make_valid_input(self) -> dict[str, callable]:
        """Create valid partitioned input with 2 Jekyll posts."""
        posts = {
            f"2023-0{i}-01-test-post-{i}.md": _make_jekyll_post(
                title=f"Test Post {i}",
                date=f"2023-0{i}-01",
                body=f"Content for test post number {i} with sufficient length.",
            )
            for i in range(1, 3)
        }
        return _make_partitioned_input(posts)

    def test_existing_output_ignored(self):
        """existing_output が渡されても parse_jekyll は全アイテムを処理すること。"""
        partitioned = self._make_valid_input()

        # First run
        first_result = parse_jekyll(partitioned)
        self.assertEqual(len(first_result), 2)

        # Simulate existing output
        existing_output = {key: (lambda v=val: v) for key, val in first_result.items()}

        # Second run: existing_output should be ignored
        second_result = parse_jekyll(partitioned, existing_output=existing_output)
        self.assertEqual(len(second_result), 2)

    def test_no_existing_output_arg(self):
        """existing_output 引数なし（デフォルト）で正常に動作すること。"""
        partitioned = self._make_valid_input()
        result = parse_jekyll(partitioned)
        self.assertEqual(len(result), 2)

    def test_empty_existing_output(self):
        """existing_output が空 dict の場合、全アイテムが処理されること。"""
        partitioned = self._make_valid_input()
        result = parse_jekyll(partitioned, existing_output={})
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# TestEmptyInputGithub: Edge cases for empty/invalid input
# ---------------------------------------------------------------------------


class TestEmptyInputGithub(unittest.TestCase):
    """parse_jekyll: edge cases for empty/invalid input."""

    def test_empty_partitioned_input(self):
        """空の partitioned_input が空 dict を返すこと。"""
        result = parse_jekyll({})
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_non_markdown_files_skipped(self):
        """非 Markdown ファイルがスキップされること。"""
        partitioned = _make_partitioned_input(
            {
                "readme.txt": "This is not a markdown file",
                "2023-01-01-valid.md": _make_jekyll_post(
                    title="Valid Post",
                    date="2023-01-01",
                    body="Valid post body with enough content.",
                ),
            }
        )

        result = parse_jekyll(partitioned)

        # Only .md file should be processed
        self.assertEqual(len(result), 1)

    def test_post_without_frontmatter(self):
        """frontmatter がないファイルでも処理されること。"""
        content = "## Just a heading\n\nSome content without frontmatter."

        partitioned = _make_partitioned_input(
            {
                "2023-06-01-no-frontmatter.md": content,
            }
        )

        result = parse_jekyll(partitioned)

        # Should still produce a result (with defaults)
        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertIsNotNone(item["content"])

    def test_unicode_content(self):
        """Unicode コンテンツが正しく処理されること。"""
        post = _make_jekyll_post(
            title="MySQL DDL",
            date="2023-10-01",
            body="## MySQL DDL\n\nOnline DDL is powerful.",
        )

        partitioned = _make_partitioned_input(
            {
                "2023-10-01-unicode-test.md": post,
            }
        )

        result = parse_jekyll(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertIn("MySQL DDL", item["conversation_name"])


if __name__ == "__main__":
    unittest.main()
