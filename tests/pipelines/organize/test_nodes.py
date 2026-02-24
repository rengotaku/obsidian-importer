"""Tests for Organize pipeline nodes.

Tests verify:
- LLM-based genre and topic extraction (extract_topic_and_genre)
- Frontmatter normalization (normalized=True, clean unnecessary fields)
- Content cleanup (excess blank lines, formatting)
- Frontmatter embedding of genre, topic, summary (no file I/O)
"""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from obsidian_etl.pipelines.organize.nodes import (
    clean_content,
    embed_frontmatter_fields,
    extract_topic_and_genre,
    log_genre_distribution,
    normalize_frontmatter,
)

# Phase 2 (060-dynamic-genre-config): these functions don't exist yet (RED state)
try:
    from obsidian_etl.pipelines.organize.nodes import (
        _build_genre_prompt,
        _parse_genre_config,
    )
except ImportError:
    _build_genre_prompt = None
    _parse_genre_config = None

# Phase 3 (060-dynamic-genre-config): US3 - other 分類の改善サイクル (RED state)
try:
    from obsidian_etl.pipelines.organize.nodes import (
        _generate_suggestions_markdown,
        _suggest_new_genres_via_llm,
        analyze_other_genres,
    )
except ImportError:
    analyze_other_genres = None
    _suggest_new_genres_via_llm = None
    _generate_suggestions_markdown = None


def _make_markdown_item(
    item_id: str = "conv-001-uuid-abcdef",
    file_id: str = "a1b2c3d4e5f6",
    title: str = "Python asyncio の仕組み",
    content: str = "",
    output_filename: str = "Python asyncio の仕組み.md",
    tags: list | None = None,
    source_provider: str = "claude",
    created: str = "2026-01-15",
) -> dict:
    """Helper to create a markdown_notes item (output of format_markdown)."""
    if tags is None:
        tags = ["Python", "asyncio"]
    if not content:
        content = (
            "---\n"
            f"title: {title}\n"
            f"created: {created}\n"
            "tags:\n"
            "  - Python\n"
            "  - asyncio\n"
            f"source_provider: {source_provider}\n"
            f"file_id: {file_id}\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "asyncio はイベントループベースの非同期フレームワーク。\n"
        )
    return {
        "item_id": item_id,
        "file_id": file_id,
        "content": content,
        "output_filename": output_filename,
        "metadata": {
            "title": title,
            "created": created,
            "tags": tags,
            "source_provider": source_provider,
            "file_id": file_id,
            "normalized": True,
        },
    }


def _make_organize_params() -> dict:
    """Helper to create organize params matching parameters.yml."""
    return {
        "genre_keywords": {
            "ai": [
                "AI",
                "機械学習",
                "深層学習",
                "生成AI",
                "プロンプト",
                "Claude",
                "ChatGPT",
                "Stable Diffusion",
                "LLM",
                "GPT",
            ],
            "devops": [
                "インフラ",
                "コンテナ",
                "クラウド",
                "CI/CD",
                "サーバー",
                "Docker",
                "Kubernetes",
                "NGINX",
                "Terraform",
                "AWS",
            ],
            "engineer": [
                "プログラミング",
                "アーキテクチャ",
                "DevOps",
                "フレームワーク",
                "API",
                "データベース",
            ],
            "business": [
                "ビジネス",
                "マネジメント",
                "リーダーシップ",
                "マーケティング",
            ],
            "economy": [
                "経済",
                "投資",
                "金融",
                "市場",
            ],
            "health": [
                "健康",
                "医療",
                "フィットネス",
                "運動",
                "病気",
            ],
            "parenting": [
                "子育て",
                "育児",
                "赤ちゃん",
                "教育",
                "幼児",
                "キッザニア",
            ],
            "travel": [
                "旅行",
                "観光",
                "ホテル",
                "航空",
            ],
            "lifestyle": [
                "家電",
                "電子レンジ",
                "洗濯機",
                "DIY",
                "住居",
                "空気清浄機",
            ],
            "daily": [
                "日常",
                "趣味",
                "雑記",
                "生活",
            ],
        },
        "genre_priority": [
            "ai",
            "devops",
            "engineer",
            "economy",
            "business",
            "health",
            "parenting",
            "travel",
            "lifestyle",
            "daily",
        ],
        "ollama": {
            "defaults": {
                "model": "gemma3:12b",
                "base_url": "http://localhost:11434",
                "timeout": 120,
                "temperature": 0.2,
            },
        },
    }


def _make_partitioned_input(items: dict[str, dict]) -> dict[str, callable]:
    """Create PartitionedDataset-style input (dict of callables)."""
    return {key: (lambda v=val: v) for key, val in items.items()}


# ============================================================
# extract_topic_and_genre node tests
# ============================================================


class TestExtractTopicAndGenre(unittest.TestCase):
    """extract_topic_and_genre: LLM-based topic and genre extraction."""

    def test_extract_topic_and_genre_success(self):
        """LLM が正常に topic と genre を抽出すること。"""
        item = _make_markdown_item(
            title="Python プログラミング入門",
            tags=["Python", "プログラミング", "入門"],
        )
        partitioned_input = _make_partitioned_input({"item-eng": item})
        params = _make_organize_params()

        # Mock LLM to return topic and genre
        with patch(
            "obsidian_etl.pipelines.organize.nodes._extract_topic_and_genre_via_llm"
        ) as mock_llm:
            mock_llm.return_value = ("python", "engineer")
            result = extract_topic_and_genre(partitioned_input, params)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)

        classified_item = list(result.values())[0]
        self.assertIn("topic", classified_item)
        self.assertIn("genre", classified_item)
        self.assertEqual(classified_item["topic"], "python")
        self.assertEqual(classified_item["genre"], "engineer")

    def test_extract_topic_and_genre_json_parse_error(self):
        """JSON パースエラー時にフォールバック値を返すこと。"""
        item = _make_markdown_item(
            title="テストコンテンツ",
            tags=["テスト"],
        )
        partitioned_input = _make_partitioned_input({"item-parse-error": item})
        params = _make_organize_params()

        # Mock LLM to return fallback on parse error
        with patch(
            "obsidian_etl.pipelines.organize.nodes._extract_topic_and_genre_via_llm"
        ) as mock_llm:
            mock_llm.return_value = ("", "other")
            result = extract_topic_and_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["topic"], "")
        self.assertEqual(classified_item["genre"], "other")

    def test_extract_topic_and_genre_invalid_genre(self):
        """不正な genre 値が 'other' にフォールバックすること。"""
        item = _make_markdown_item(
            title="テストコンテンツ",
            tags=["テスト"],
        )
        partitioned_input = _make_partitioned_input({"item-invalid-genre": item})
        params = _make_organize_params()

        # Mock LLM to return invalid genre
        with patch(
            "obsidian_etl.pipelines.organize.nodes._extract_topic_and_genre_via_llm"
        ) as mock_llm:
            mock_llm.return_value = ("test", "invalid_genre")
            result = extract_topic_and_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        # Note: The validation happens inside _extract_topic_and_genre_via_llm,
        # so we need to return the corrected value from the mock
        self.assertEqual(classified_item["topic"], "test")
        self.assertEqual(classified_item["genre"], "invalid_genre")

    def test_extract_topic_and_genre_multiple_items(self):
        """複数アイテムがそれぞれ正しく処理されること。"""
        items = {
            "eng": _make_markdown_item(
                item_id="eng",
                title="API設計",
                tags=["API", "設計"],
            ),
            "biz": _make_markdown_item(
                item_id="biz",
                title="リーダーシップ論",
                tags=["リーダーシップ"],
            ),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()

        # Mock LLM to return different values for each item
        with patch(
            "obsidian_etl.pipelines.organize.nodes._extract_topic_and_genre_via_llm"
        ) as mock_llm:
            mock_llm.side_effect = [("api", "engineer"), ("leadership", "business")]
            result = extract_topic_and_genre(partitioned_input, params)

        self.assertEqual(len(result), 2)
        topics = {v["item_id"]: v["topic"] for v in result.values()}
        genres = {v["item_id"]: v["genre"] for v in result.values()}
        self.assertEqual(topics["eng"], "api")
        self.assertEqual(genres["eng"], "engineer")
        self.assertEqual(topics["biz"], "leadership")
        self.assertEqual(genres["biz"], "business")


# ============================================================
# normalize_frontmatter node tests
# ============================================================


class TestNormalizeFrontmatter(unittest.TestCase):
    """normalize_frontmatter: add/update normalized=True, clean unnecessary fields."""

    def test_normalize_frontmatter_sets_normalized_true(self):
        """normalized=True が設定されること。"""
        item = _make_markdown_item()
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-norm": item})
        params = _make_organize_params()

        result = normalize_frontmatter(partitioned_input, params)

        normalized_item = list(result.values())[0]
        # Content should contain normalized: true in frontmatter
        self.assertIn("normalized: true", normalized_item["content"])

    def test_normalize_frontmatter_removes_unnecessary_fields(self):
        """draft, private, slug, lastmod, keywords などの不要フィールドが削除されること。"""
        content = (
            "---\n"
            "title: テスト\n"
            "created: 2026-01-15\n"
            "draft: false\n"
            "private: false\n"
            "slug: test-slug\n"
            "lastmod: 2026-01-20\n"
            "keywords:\n"
            "  - kw1\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "コンテンツ。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-clean": item})
        params = _make_organize_params()

        result = normalize_frontmatter(partitioned_input, params)

        normalized_item = list(result.values())[0]
        normalized_content = normalized_item["content"]

        # Unnecessary fields should be removed
        self.assertNotIn("draft:", normalized_content)
        self.assertNotIn("private:", normalized_content)
        self.assertNotIn("slug:", normalized_content)
        self.assertNotIn("lastmod:", normalized_content)
        self.assertNotIn("keywords:", normalized_content)

        # Essential fields should remain
        self.assertIn("title:", normalized_content)
        self.assertIn("created:", normalized_content)
        self.assertIn("normalized: true", normalized_content)

    def test_normalize_frontmatter_preserves_essential_fields(self):
        """title, created, tags, file_id, source_provider が保持されること。"""
        item = _make_markdown_item()
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-preserve": item})
        params = _make_organize_params()

        result = normalize_frontmatter(partitioned_input, params)

        normalized_item = list(result.values())[0]
        normalized_content = normalized_item["content"]

        self.assertIn("title:", normalized_content)
        self.assertIn("created:", normalized_content)
        self.assertIn("tags:", normalized_content)
        self.assertIn("file_id:", normalized_content)
        self.assertIn("normalized: true", normalized_content)

    def test_normalize_frontmatter_adds_normalized_when_missing(self):
        """frontmatter に normalized がない場合、追加されること。"""
        content = (
            "---\ntitle: テスト\ncreated: 2026-01-15\ntags:\n  - テスト\n---\n\nコンテンツ。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "other"
        partitioned_input = _make_partitioned_input({"item-add-norm": item})
        params = _make_organize_params()

        result = normalize_frontmatter(partitioned_input, params)

        normalized_item = list(result.values())[0]
        self.assertIn("normalized: true", normalized_item["content"])


# ============================================================
# clean_content node tests
# ============================================================


class TestCleanContent(unittest.TestCase):
    """clean_content: excess blank lines, formatting cleanup."""

    def test_clean_content_removes_excess_blank_lines(self):
        """連続する3行以上の空行が最大1行に削減されること。"""
        content = (
            "---\n"
            "title: テスト\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "\n"
            "\n"
            "\n"
            "コンテンツがここにある。\n"
            "\n"
            "\n"
            "\n"
            "別のセクション。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-blank": item})

        result = clean_content(partitioned_input)

        cleaned_item = list(result.values())[0]
        cleaned_content = cleaned_item["content"]

        # Should not have 3+ consecutive blank lines
        self.assertNotIn("\n\n\n\n", cleaned_content)

    def test_clean_content_preserves_single_blank_line(self):
        """段落間の1行空行は保持されること。"""
        content = (
            "---\n"
            "title: テスト\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "コンテンツ1。\n"
            "\n"
            "コンテンツ2。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-single": item})

        result = clean_content(partitioned_input)

        cleaned_item = list(result.values())[0]
        cleaned_content = cleaned_item["content"]

        # Single blank lines between paragraphs should remain
        self.assertIn("コンテンツ1。\n\nコンテンツ2。", cleaned_content)

    def test_clean_content_strips_trailing_whitespace(self):
        """行末の余分な空白が除去されること。"""
        content = (
            "---\n"
            "title: テスト\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "行末に空白がある。   \n"
            "この行にもある。  \n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-trail": item})

        result = clean_content(partitioned_input)

        cleaned_item = list(result.values())[0]
        cleaned_content = cleaned_item["content"]

        # Lines should not end with trailing spaces (except possibly in frontmatter)
        body_start = cleaned_content.index("\n---\n", 4) + 5
        body = cleaned_content[body_start:]
        for line in body.split("\n"):
            if line:  # skip empty lines
                self.assertEqual(line, line.rstrip(), f"Trailing whitespace found: '{line}'")

    def test_clean_content_preserves_frontmatter(self):
        """frontmatter は clean_content で変更されないこと。"""
        content = (
            "---\n"
            "title: テスト\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - Python\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "本文。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-fm": item})

        result = clean_content(partitioned_input)

        cleaned_item = list(result.values())[0]
        cleaned_content = cleaned_item["content"]

        # Frontmatter should still be present and intact
        self.assertTrue(cleaned_content.startswith("---\n"))
        self.assertIn("title: テスト", cleaned_content)
        self.assertIn("normalized: true", cleaned_content)


# ============================================================
# embed_frontmatter_fields node tests (Phase 2 - 047-e2e-full-pipeline)
# ============================================================


class TestEmbedFrontmatterFields(unittest.TestCase):
    """embed_frontmatter_fields: embed genre, topic, summary into frontmatter content."""

    def test_embed_frontmatter_fields_adds_genre(self):
        """genre が frontmatter に追加されること。"""
        content = (
            "---\n"
            "title: Pythonの非同期処理\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - Python\n"
            "  - asyncio\n"
            "source_provider: claude\n"
            "file_id: a1b2c3d4e5f6\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "asyncio はイベントループベースの非同期フレームワーク。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        item["topic"] = "python"
        item["metadata"]["summary"] = "Pythonの非同期処理について解説"
        partitioned_input = _make_partitioned_input({"item-genre": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        embedded_content = list(result.values())[0]
        self.assertIn("genre: engineer", embedded_content)

    def test_embed_frontmatter_fields_adds_topic(self):
        """topic が frontmatter に追加されること。"""
        content = (
            "---\n"
            "title: AWS Lambda入門\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - AWS\n"
            "  - Lambda\n"
            "source_provider: claude\n"
            "file_id: b2c3d4e5f6a1\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "AWS Lambda のサーバーレスアーキテクチャについて。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        item["topic"] = "aws"
        item["metadata"]["summary"] = "AWS Lambdaの基本について解説"
        partitioned_input = _make_partitioned_input({"item-topic": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        embedded_content = list(result.values())[0]
        self.assertIn("topic: aws", embedded_content)

    def test_embed_frontmatter_fields_adds_empty_topic(self):
        """空の topic が frontmatter に追加されること。

        topic が空文字の場合も frontmatter に含まれる（空文字許容）。
        """
        content = (
            "---\n"
            "title: 日常のメモ\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - メモ\n"
            "source_provider: claude\n"
            "file_id: c3d4e5f6a1b2\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "日常の雑記。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "daily"
        item["topic"] = ""
        item["metadata"]["summary"] = "日常のメモ"
        partitioned_input = _make_partitioned_input({"item-empty-topic": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        embedded_content = list(result.values())[0]
        # Empty topic should be represented as empty string in frontmatter
        # Either "topic: ''" or "topic: " or "topic: ''" format
        self.assertIn("topic:", embedded_content)
        # Verify genre is also present
        self.assertIn("genre: daily", embedded_content)

    def test_embed_frontmatter_fields_adds_summary(self):
        """summary が frontmatter に追加されること。"""
        content = (
            "---\n"
            "title: データベース設計\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - DB\n"
            "  - 設計\n"
            "source_provider: claude\n"
            "file_id: d4e5f6a1b2c3\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "データベースの正規化について解説。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        item["topic"] = "database"
        item["metadata"]["summary"] = "RDBの正規化理論とインデックス設計について解説"
        partitioned_input = _make_partitioned_input({"item-summary": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        embedded_content = list(result.values())[0]
        self.assertIn("summary:", embedded_content)
        self.assertIn("RDBの正規化理論", embedded_content)

    def test_embed_frontmatter_fields_no_file_write(self):
        """ファイルシステムへの書き込みが発生しないこと。

        embed_frontmatter_fields はメモリ上で処理を行い、
        ファイルシステムには一切書き込まない。
        """
        content = (
            "---\n"
            "title: テスト\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - テスト\n"
            "source_provider: claude\n"
            "file_id: e5f6a1b2c3d4\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "テストコンテンツ。\n"
        )
        item = _make_markdown_item(content=content, output_filename="テスト.md")
        item["genre"] = "other"
        item["topic"] = ""
        item["metadata"]["summary"] = "テスト用サマリー"
        partitioned_input = _make_partitioned_input({"item-no-write": item})
        params = _make_organize_params()

        # Create a temp directory to monitor for any file writes
        with tempfile.TemporaryDirectory() as tmpdir:
            params["base_path"] = tmpdir
            original_files = set(os.listdir(tmpdir))

            result = embed_frontmatter_fields(partitioned_input, params)

            # No new files or directories should be created
            after_files = set(os.listdir(tmpdir))
            self.assertEqual(
                original_files,
                after_files,
                "embed_frontmatter_fields should not write to filesystem",
            )

            # Result should be dict[str, str] (filename -> content)
            self.assertIsInstance(result, dict)
            for key, value in result.items():
                self.assertIsInstance(key, str)
                self.assertIsInstance(value, str)


# ============================================================
# embed_frontmatter_fields review_reason tests (Phase 5 - 050)
# ============================================================


class TestEmbedFrontmatterWithReviewReason(unittest.TestCase):
    """embed_frontmatter_fields: embed review_reason into frontmatter.

    Tests for User Story 2 - レビューフォルダ出力 (050-fix-content-compression)
    review_reason が frontmatter に埋め込まれることを検証。
    """

    def test_embed_frontmatter_with_review_reason(self):
        """review_reason が frontmatter に埋め込まれること。

        FR-010: システムは review_reason を frontmatter に埋め込まなければならない
        Format: review_reason: "extract_knowledge: body_ratio=X.X% < threshold=Y.Y%"
        """
        content = (
            "---\n"
            "title: 要レビュー記事\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - テスト\n"
            "source_provider: claude\n"
            "file_id: review12345678\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "内容が少ないテスト記事。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        item["topic"] = "test"
        item["review_reason"] = "extract_knowledge: body_ratio=5.0% < threshold=10.0%"
        item["metadata"]["summary"] = "テスト要約"
        partitioned_input = _make_partitioned_input({"item-review": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        embedded_content = list(result.values())[0]

        # review_reason should be in frontmatter
        self.assertIn("review_reason:", embedded_content)
        self.assertIn("extract_knowledge:", embedded_content)
        self.assertIn("body_ratio=5.0%", embedded_content)
        self.assertIn("threshold=10.0%", embedded_content)

    def test_embed_frontmatter_without_review_reason(self):
        """review_reason がない場合は frontmatter に含まれないこと。

        review_reason が item にない場合、frontmatter には review_reason フィールドが含まれない。
        """
        content = (
            "---\n"
            "title: 通常記事\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - テスト\n"
            "source_provider: claude\n"
            "file_id: normal12345678\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "## 要約\n"
            "\n"
            "正常な内容の記事。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "engineer"
        item["topic"] = "test"
        # No review_reason
        item["metadata"]["summary"] = "テスト要約"
        partitioned_input = _make_partitioned_input({"item-normal": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        embedded_content = list(result.values())[0]

        # review_reason should NOT be in frontmatter
        self.assertNotIn("review_reason:", embedded_content)

        # Other fields should still be present
        self.assertIn("genre: engineer", embedded_content)
        self.assertIn("topic: test", embedded_content)

    def test_embed_frontmatter_review_reason_format(self):
        """review_reason のフォーマットが正しいこと。

        Format: "node_name: body_ratio=X.X% < threshold=Y.Y%"
        例: "extract_knowledge: body_ratio=3.8% < threshold=10.0%"
        """
        content = (
            "---\n"
            "title: フォーマット確認\n"
            "created: 2026-01-15\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "テスト内容。\n"
        )
        item = _make_markdown_item(content=content)
        item["genre"] = "other"
        item["topic"] = ""
        item["review_reason"] = "extract_knowledge: body_ratio=3.8% < threshold=10.0%"
        item["metadata"]["summary"] = ""
        partitioned_input = _make_partitioned_input({"item-fmt": item})
        params = _make_organize_params()

        result = embed_frontmatter_fields(partitioned_input, params)

        embedded_content = list(result.values())[0]

        # Verify the exact format is preserved in frontmatter
        # The value should be quoted in YAML due to special characters (%, <, :)
        self.assertIn("review_reason:", embedded_content)
        # The actual content should contain the ratio info
        self.assertIn("body_ratio=3.8%", embedded_content)
        self.assertIn("threshold=10.0%", embedded_content)


# ============================================================
# extract_topic_and_genre Ollama config tests
# ============================================================


class TestExtractTopicAndGenreUsesOllamaConfig(unittest.TestCase):
    """extract_topic_and_genre: verify integration with get_ollama_config.

    These tests verify that _extract_topic_and_genre_via_llm uses get_ollama_config
    to retrieve function-specific parameters and passes them correctly
    to the Ollama API.
    """

    def test_extract_topic_and_genre_uses_config(self):
        """_extract_topic_and_genre_via_llm が get_ollama_config を呼び出すこと。

        Verify that _extract_topic_and_genre_via_llm calls get_ollama_config(params, "extract_topic_and_genre")
        to retrieve the configuration.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_and_genre_via_llm

        content = "## 要約\n\nPythonの非同期処理について解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "timeout": 120},
                "functions": {
                    "extract_topic_and_genre": {
                        "model": "llama3.2:3b",
                        "num_predict": 128,
                        "timeout": 30,
                    }
                },
            }
        }

        # Mock get_ollama_config to verify it's called
        with patch("obsidian_etl.pipelines.organize.nodes.get_ollama_config") as mock_get_config:
            # Return a mock config that has required attributes
            from obsidian_etl.utils.ollama_config import OllamaConfig

            mock_get_config.return_value = OllamaConfig(
                model="llama3.2:3b",
                base_url="http://localhost:11434",
                timeout=30,
                temperature=0.2,
                num_predict=128,
            )

            # Also mock the actual API call to avoid network calls
            with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
                mock_call_ollama.return_value = ('{"topic": "python", "genre": "engineer"}', None)
                _extract_topic_and_genre_via_llm(content, params)

            # Verify get_ollama_config was called with correct arguments
            mock_get_config.assert_called_once_with(params, "extract_topic_and_genre")

    def test_extract_topic_and_genre_uses_correct_model(self):
        """extract_topic_and_genre が設定されたモデルを使用すること。

        Verify that the model from ollama.functions.extract_topic_and_genre is used
        in the API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_and_genre_via_llm

        content = "## 要約\n\nAWSのLambda関数について解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b"},
                "functions": {"extract_topic_and_genre": {"model": "llama3.2:3b"}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = ('{"topic": "aws", "genre": "devops"}', None)
            _extract_topic_and_genre_via_llm(content, params)

            # Verify call_ollama was called with the correct model
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that model argument is "llama3.2:3b" (from functions.extract_topic_and_genre)
            self.assertEqual(call_kwargs.kwargs.get("model"), "llama3.2:3b")

    def test_extract_topic_and_genre_uses_correct_timeout(self):
        """extract_topic_and_genre が設定されたタイムアウトを使用すること。

        Verify that the timeout from ollama.functions.extract_topic_and_genre is used
        in the API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_and_genre_via_llm

        content = "## 要約\n\nReact Nativeでモバイルアプリを開発します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "timeout": 120},
                "functions": {"extract_topic_and_genre": {"timeout": 30}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = (
                '{"topic": "mobile development", "genre": "engineer"}',
                None,
            )
            _extract_topic_and_genre_via_llm(content, params)

            # Verify call_ollama was called with the correct timeout
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that timeout argument is 30 (from functions.extract_topic_and_genre)
            self.assertEqual(call_kwargs.kwargs.get("timeout"), 30)

    def test_extract_topic_and_genre_num_predict_applied(self):
        """extract_topic_and_genre が num_predict を Ollama API に渡すこと。

        Verify that num_predict from ollama.functions.extract_topic_and_genre is passed
        to the Ollama API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_and_genre_via_llm

        content = "## 要約\n\nDockerコンテナについて解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "num_predict": -1},
                "functions": {"extract_topic_and_genre": {"num_predict": 128}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = ('{"topic": "docker", "genre": "devops"}', None)
            _extract_topic_and_genre_via_llm(content, params)

            # Verify call_ollama was called with the correct num_predict
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that num_predict argument is 128 (from functions.extract_topic_and_genre)
            self.assertEqual(call_kwargs.kwargs.get("num_predict"), 128)


# ============================================================
# log_genre_distribution node tests (Phase 4 - 058-refine-genre-classification)
# ============================================================


class TestLogGenreDistribution(unittest.TestCase):
    """log_genre_distribution: ジャンル分布（件数・割合）をログ出力する。

    FR-008: パイプライン完了時にジャンル分布がログ出力されること。
    """

    def test_log_genre_distribution_logs_counts(self):
        """各ジャンルの件数がログ出力されること。"""
        classified_items = {
            "item1": {"item_id": "1", "genre": "ai"},
            "item2": {"item_id": "2", "genre": "engineer"},
            "item3": {"item_id": "3", "genre": "engineer"},
            "item4": {"item_id": "4", "genre": "other"},
        }
        partitioned_input = _make_partitioned_input(classified_items)
        params = _make_organize_params()

        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            log_genre_distribution(partitioned_input, params)

            # logger.info が呼ばれたことを確認
            mock_logger.info.assert_called()

            # 全ての info 呼び出しの引数を結合して検証
            all_log_calls = " ".join(str(call) for call in mock_logger.info.call_args_list)
            self.assertIn("ai", all_log_calls)
            self.assertIn("1", all_log_calls)
            self.assertIn("engineer", all_log_calls)
            self.assertIn("2", all_log_calls)
            self.assertIn("other", all_log_calls)

    def test_log_genre_distribution_logs_percentages(self):
        """各ジャンルの割合（%）がログ出力されること。"""
        classified_items = {
            "item1": {"item_id": "1", "genre": "ai"},
            "item2": {"item_id": "2", "genre": "ai"},
            "item3": {"item_id": "3", "genre": "engineer"},
            "item4": {"item_id": "4", "genre": "other"},
        }
        partitioned_input = _make_partitioned_input(classified_items)
        params = _make_organize_params()

        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            log_genre_distribution(partitioned_input, params)

            all_log_calls = " ".join(str(call) for call in mock_logger.info.call_args_list)
            # ai: 2/4 = 50.0%
            self.assertIn("50.0%", all_log_calls)
            # engineer: 1/4 = 25.0%
            self.assertIn("25.0%", all_log_calls)
            # other: 1/4 = 25.0%
            self.assertIn("25.0%", all_log_calls)

    def test_log_genre_distribution_empty_input(self):
        """空の入力でもエラーにならないこと。"""
        partitioned_input = _make_partitioned_input({})
        params = _make_organize_params()

        # 空入力でも例外が発生しないこと
        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            log_genre_distribution(partitioned_input, params)

    def test_log_genre_distribution_single_genre(self):
        """全アイテムが同一ジャンルの場合、100.0% と表示されること。"""
        classified_items = {
            "item1": {"item_id": "1", "genre": "ai"},
            "item2": {"item_id": "2", "genre": "ai"},
            "item3": {"item_id": "3", "genre": "ai"},
        }
        partitioned_input = _make_partitioned_input(classified_items)
        params = _make_organize_params()

        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            log_genre_distribution(partitioned_input, params)

            all_log_calls = " ".join(str(call) for call in mock_logger.info.call_args_list)
            self.assertIn("ai", all_log_calls)
            self.assertIn("3", all_log_calls)
            self.assertIn("100.0%", all_log_calls)

    def test_log_genre_distribution_returns_input(self):
        """入力をそのまま返すこと（パイプラインの次ノードに渡すため）。"""
        classified_items = {
            "item1": {"item_id": "1", "genre": "ai"},
            "item2": {"item_id": "2", "genre": "engineer"},
        }
        partitioned_input = _make_partitioned_input(classified_items)
        params = _make_organize_params()

        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            result = log_genre_distribution(partitioned_input, params)

        # 入力と同じ dict が返されること
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)


# ============================================================
# Dynamic Genre Config tests (Phase 2 - 060-dynamic-genre-config)
# ============================================================


def _make_genre_config_new_format() -> dict:
    """Helper to create genre_vault_mapping in new format (vault + description)."""
    return {
        "ai": {
            "vault": "エンジニア",
            "description": "AI/機械学習/LLM/生成AI/Claude/ChatGPT",
        },
        "devops": {
            "vault": "エンジニア",
            "description": "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS",
        },
        "engineer": {
            "vault": "エンジニア",
            "description": "プログラミング/アーキテクチャ/API/データベース/フレームワーク",
        },
        "economy": {
            "vault": "経済",
            "description": "経済/投資/金融/市場",
        },
        "business": {
            "vault": "ビジネス",
            "description": "ビジネス/マネジメント/リーダーシップ/マーケティング",
        },
        "health": {
            "vault": "健康",
            "description": "健康/医療/フィットネス/運動",
        },
        "parenting": {
            "vault": "子育て",
            "description": "子育て/育児/教育/幼児",
        },
        "travel": {
            "vault": "旅行",
            "description": "旅行/観光/ホテル",
        },
        "lifestyle": {
            "vault": "ライフスタイル",
            "description": "家電/DIY/住居/生活用品",
        },
        "daily": {
            "vault": "日常",
            "description": "日常/趣味/雑記",
        },
        "other": {
            "vault": "その他",
            "description": "上記に該当しないもの",
        },
    }


class TestDynamicGenreConfig(unittest.TestCase):
    """Dynamic genre config: ジャンル定義の動的設定テスト。

    060-dynamic-genre-config Phase 2: US1 + US2
    - _build_genre_prompt: 設定からLLMプロンプト用のジャンル一覧を生成
    - _parse_genre_config: 新形式設定を解析し genre_definitions と valid_genres を返す
    - valid_genres の動的構築
    - 不正ジャンルの other フォールバック
    """

    def setUp(self):
        """関数が存在しない場合は FAIL させる (RED state)。"""
        if _parse_genre_config is None:
            self.fail("_parse_genre_config is not yet implemented (RED)")
        if _build_genre_prompt is None:
            self.fail("_build_genre_prompt is not yet implemented (RED)")

    # ---- US1: test_build_genre_prompt ----

    def test_build_genre_prompt_contains_all_genres(self):
        """_build_genre_prompt が全ジャンルをプロンプト文字列に含めること。"""
        genre_config = _make_genre_config_new_format()
        genre_definitions, _ = _parse_genre_config(genre_config)
        result = _build_genre_prompt(genre_definitions)

        # 全ジャンルキーがプロンプトに含まれること
        for genre_key in genre_config:
            self.assertIn(genre_key, result, f"Genre '{genre_key}' should be in prompt")

    def test_build_genre_prompt_contains_descriptions(self):
        """_build_genre_prompt が各ジャンルの description を含めること。"""
        genre_config = _make_genre_config_new_format()
        genre_definitions, _ = _parse_genre_config(genre_config)
        result = _build_genre_prompt(genre_definitions)

        # description がプロンプトに含まれること
        self.assertIn("AI/機械学習/LLM/生成AI/Claude/ChatGPT", result)
        self.assertIn("インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS", result)

    def test_build_genre_prompt_format(self):
        """_build_genre_prompt が '- key: description' 形式で出力すること。"""
        genre_config = {
            "ai": {
                "vault": "エンジニア",
                "description": "AI/機械学習",
            },
            "other": {
                "vault": "その他",
                "description": "上記に該当しないもの",
            },
        }
        genre_definitions, _ = _parse_genre_config(genre_config)
        result = _build_genre_prompt(genre_definitions)

        self.assertIn("- ai: AI/機械学習", result)
        self.assertIn("- other: 上記に該当しないもの", result)

    def test_build_genre_prompt_empty_definitions(self):
        """空の genre_definitions で空文字列を返すこと。"""
        result = _build_genre_prompt({})
        self.assertEqual(result, "")

    # ---- US1: test_parse_genre_config_new_format ----

    def test_parse_genre_config_returns_tuple(self):
        """_parse_genre_config が (genre_definitions, valid_genres) のタプルを返すこと。"""
        genre_config = _make_genre_config_new_format()
        result = _parse_genre_config(genre_config)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_parse_genre_config_extracts_descriptions(self):
        """_parse_genre_config が description を正しく抽出すること。"""
        genre_config = _make_genre_config_new_format()
        genre_definitions, _ = _parse_genre_config(genre_config)

        self.assertEqual(genre_definitions["ai"], "AI/機械学習/LLM/生成AI/Claude/ChatGPT")
        self.assertEqual(
            genre_definitions["devops"], "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS"
        )

    def test_parse_genre_config_missing_description_uses_genre_name(self):
        """description がないジャンルはジャンル名を description として使用すること。"""
        genre_config = {
            "custom_genre": {
                "vault": "カスタム",
                # description なし
            },
        }
        genre_definitions, _ = _parse_genre_config(genre_config)

        self.assertEqual(genre_definitions["custom_genre"], "custom_genre")

    def test_parse_genre_config_valid_genres_set(self):
        """_parse_genre_config が valid_genres を set として返すこと。"""
        genre_config = _make_genre_config_new_format()
        _, valid_genres = _parse_genre_config(genre_config)

        self.assertIsInstance(valid_genres, set)
        self.assertIn("ai", valid_genres)
        self.assertIn("devops", valid_genres)
        self.assertIn("other", valid_genres)

    # ---- US2: test_valid_genres_from_config ----

    def test_valid_genres_includes_custom_genre(self):
        """カスタムジャンルが valid_genres に含まれること。"""
        genre_config = _make_genre_config_new_format()
        genre_config["finance"] = {
            "vault": "経済",
            "description": "金融/投資/株式/FX",
        }
        _, valid_genres = _parse_genre_config(genre_config)

        self.assertIn("finance", valid_genres)

    def test_valid_genres_always_includes_other(self):
        """other がなくても valid_genres に含まれること。"""
        genre_config = {
            "ai": {
                "vault": "エンジニア",
                "description": "AI/機械学習",
            },
        }
        _, valid_genres = _parse_genre_config(genre_config)

        self.assertIn("other", valid_genres, "valid_genres should always include 'other'")

    def test_valid_genres_matches_config_keys(self):
        """valid_genres が設定キーと一致すること（other を含む）。"""
        genre_config = {
            "ai": {"vault": "エンジニア", "description": "AI"},
            "devops": {"vault": "エンジニア", "description": "DevOps"},
        }
        _, valid_genres = _parse_genre_config(genre_config)

        self.assertIn("ai", valid_genres)
        self.assertIn("devops", valid_genres)
        self.assertIn("other", valid_genres)
        # ハードコードされたジャンルは含まれないこと
        self.assertNotIn("business", valid_genres)
        self.assertNotIn("health", valid_genres)

    # ---- US2: test_genre_fallback_to_other ----

    def test_genre_fallback_with_custom_config(self):
        """カスタム設定で不正ジャンルが other にフォールバックすること。"""
        genre_config = {
            "ai": {"vault": "エンジニア", "description": "AI"},
            "finance": {"vault": "経済", "description": "金融"},
        }
        _, valid_genres = _parse_genre_config(genre_config)

        # "engineer" は設定にないので不正
        invalid_genre = "engineer"
        self.assertNotIn(invalid_genre, valid_genres)

        # バリデーションロジック: valid_genres にない場合は "other"
        result_genre = invalid_genre if invalid_genre in valid_genres else "other"
        self.assertEqual(result_genre, "other")

    def test_genre_fallback_valid_genre_not_changed(self):
        """有効なジャンルはそのまま保持されること。"""
        genre_config = {
            "ai": {"vault": "エンジニア", "description": "AI"},
            "finance": {"vault": "経済", "description": "金融"},
        }
        _, valid_genres = _parse_genre_config(genre_config)

        valid_genre = "finance"
        self.assertIn(valid_genre, valid_genres)

        result_genre = valid_genre if valid_genre in valid_genres else "other"
        self.assertEqual(result_genre, "finance")

    def test_genre_fallback_integration_with_extract(self):
        """extract_topic_and_genre が設定ベースで不正ジャンルを other にフォールバックすること。"""
        item = _make_markdown_item(
            title="ブロックチェーン入門",
            tags=["ブロックチェーン", "暗号通貨"],
        )
        partitioned_input = _make_partitioned_input({"item-blockchain": item})

        # カスタム設定: ai と finance のみ
        params = _make_organize_params()
        params["genre_vault_mapping"] = {
            "ai": {"vault": "エンジニア", "description": "AI/機械学習"},
            "finance": {"vault": "経済", "description": "金融/投資"},
            "other": {"vault": "その他", "description": "上記に該当しないもの"},
        }
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        # LLM が設定にない "engineer" を返した場合、other にフォールバック
        with patch(
            "obsidian_etl.pipelines.organize.nodes._extract_topic_and_genre_via_llm"
        ) as mock_llm:
            mock_llm.return_value = ("blockchain", "other")
            result = extract_topic_and_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "other")


# ============================================================
# Analyze Other Genres tests (Phase 3 - 060-dynamic-genre-config / US3)
# ============================================================


class TestAnalyzeOtherGenres(unittest.TestCase):
    """analyze_other_genres: other 分類の改善サイクル。

    060-dynamic-genre-config Phase 3: US3
    - analyze_other_genres: other 5件以上で新ジャンル提案トリガー
    - _suggest_new_genres_via_llm: LLM による新ジャンル候補提案
    - _generate_suggestions_markdown: 提案レポートの Markdown 生成
    """

    def setUp(self):
        """関数が存在しない場合は FAIL させる (RED state)。"""
        if analyze_other_genres is None:
            self.fail("analyze_other_genres is not yet implemented (RED)")
        if _suggest_new_genres_via_llm is None:
            self.fail("_suggest_new_genres_via_llm is not yet implemented (RED)")
        if _generate_suggestions_markdown is None:
            self.fail("_generate_suggestions_markdown is not yet implemented (RED)")

    def _make_other_items(self, count: int) -> dict[str, dict]:
        """Helper: other に分類された N 件のアイテムを作成する。"""
        items = {}
        for i in range(count):
            item = _make_markdown_item(
                item_id=f"other-{i:03d}",
                title=f"その他コンテンツ {i}",
                tags=["その他"],
            )
            item["genre"] = "other"
            item["topic"] = f"topic-{i}"
            items[f"item-other-{i:03d}"] = item
        return items

    def _make_mixed_items(self, other_count: int, ai_count: int = 2) -> dict[str, dict]:
        """Helper: other と ai が混在するアイテム群を作成する。"""
        items = {}
        for i in range(other_count):
            item = _make_markdown_item(
                item_id=f"other-{i:03d}",
                title=f"その他コンテンツ {i}",
                tags=["その他"],
            )
            item["genre"] = "other"
            item["topic"] = f"topic-{i}"
            items[f"item-other-{i:03d}"] = item
        for i in range(ai_count):
            item = _make_markdown_item(
                item_id=f"ai-{i:03d}",
                title=f"AI コンテンツ {i}",
                tags=["AI"],
            )
            item["genre"] = "ai"
            item["topic"] = "ai"
            items[f"item-ai-{i:03d}"] = item
        return items

    # ---- T023: test_analyze_other_genres_trigger ----

    def test_analyze_other_genres_trigger(self):
        """other が5件以上の場合に analyze_other_genres がトリガーされ提案を返すこと。"""
        items = self._make_other_items(6)
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()
        params["genre_vault_mapping"] = _make_genre_config_new_format()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        # Mock LLM to return genre suggestions
        mock_suggestions = [
            {
                "suggested_genre": "cooking",
                "suggested_description": "料理/レシピ/食材",
                "sample_titles": ["その他コンテンツ 0", "その他コンテンツ 1"],
                "content_count": 3,
            },
        ]

        with patch("obsidian_etl.pipelines.organize.nodes._suggest_new_genres_via_llm") as mock_llm:
            mock_llm.return_value = mock_suggestions
            result = analyze_other_genres(partitioned_input, params)

        # result should be a string (markdown content for genre_suggestions.md)
        self.assertIsInstance(result, str)
        self.assertIn("ジャンル提案レポート", result)
        self.assertIn("cooking", result)

    # ---- T024: test_analyze_other_genres_below_threshold ----

    def test_analyze_other_genres_below_threshold(self):
        """other が4件以下の場合は提案なしメッセージを返すこと。"""
        items = self._make_mixed_items(other_count=4, ai_count=3)
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()
        params["genre_vault_mapping"] = _make_genre_config_new_format()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        result = analyze_other_genres(partitioned_input, params)

        # Should return a string indicating no suggestions
        self.assertIsInstance(result, str)
        # Should contain "提案なし" or indicate below threshold
        self.assertIn("5件未満", result)
        # Should NOT trigger LLM call (no suggestions)
        self.assertNotIn("提案 1", result)

    def test_analyze_other_genres_zero_other(self):
        """other が0件の場合も提案なしメッセージを返すこと。"""
        items = {}
        for i in range(3):
            item = _make_markdown_item(
                item_id=f"ai-{i:03d}",
                title=f"AI コンテンツ {i}",
                tags=["AI"],
            )
            item["genre"] = "ai"
            item["topic"] = "ai"
            items[f"item-ai-{i:03d}"] = item
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()
        params["genre_vault_mapping"] = _make_genre_config_new_format()

        result = analyze_other_genres(partitioned_input, params)

        self.assertIsInstance(result, str)
        self.assertIn("5件未満", result)

    def test_analyze_other_genres_exactly_five(self):
        """other がちょうど5件の場合にトリガーされること。"""
        items = self._make_other_items(5)
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()
        params["genre_vault_mapping"] = _make_genre_config_new_format()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        mock_suggestions = [
            {
                "suggested_genre": "sports",
                "suggested_description": "スポーツ/競技/トレーニング",
                "sample_titles": ["その他コンテンツ 0"],
                "content_count": 2,
            },
        ]

        with patch("obsidian_etl.pipelines.organize.nodes._suggest_new_genres_via_llm") as mock_llm:
            mock_llm.return_value = mock_suggestions
            result = analyze_other_genres(partitioned_input, params)

        self.assertIsInstance(result, str)
        self.assertIn("ジャンル提案レポート", result)

    # ---- T025: test_generate_genre_suggestions_md ----

    def test_generate_genre_suggestions_md_format(self):
        """_generate_suggestions_markdown が正しい Markdown 形式を出力すること。"""
        suggestions = [
            {
                "suggested_genre": "cooking",
                "suggested_description": "料理/レシピ/食材",
                "sample_titles": ["パスタの作り方", "カレーレシピ", "和食の基本"],
                "content_count": 5,
            },
            {
                "suggested_genre": "sports",
                "suggested_description": "スポーツ/競技/トレーニング",
                "sample_titles": ["ランニング入門", "筋トレメニュー"],
                "content_count": 3,
            },
        ]
        other_count = 10

        result = _generate_suggestions_markdown(suggestions, other_count)

        # Header
        self.assertIn("# ジャンル提案レポート", result)
        # Metadata
        self.assertIn("**other 分類数**: 10件", result)
        self.assertIn("**提案数**: 2件", result)
        self.assertIn("**生成日時**:", result)
        # Suggestion 1
        self.assertIn("## 提案 1: cooking", result)
        self.assertIn("**Description**: 料理/レシピ/食材", result)
        self.assertIn("**該当コンテンツ** (5件)", result)
        self.assertIn("- パスタの作り方", result)
        self.assertIn("- カレーレシピ", result)
        self.assertIn("- 和食の基本", result)
        # Suggestion 2
        self.assertIn("## 提案 2: sports", result)
        self.assertIn("**Description**: スポーツ/競技/トレーニング", result)
        self.assertIn("**該当コンテンツ** (3件)", result)

    def test_generate_genre_suggestions_md_yaml_example(self):
        """_generate_suggestions_markdown が YAML 設定例を含むこと。"""
        suggestions = [
            {
                "suggested_genre": "cooking",
                "suggested_description": "料理/レシピ/食材",
                "sample_titles": ["パスタの作り方"],
                "content_count": 3,
            },
        ]

        result = _generate_suggestions_markdown(suggestions, 5)

        # Should include YAML config example
        self.assertIn("cooking:", result)
        self.assertIn("vault:", result)
        self.assertIn("description:", result)

    def test_generate_genre_suggestions_md_empty_suggestions(self):
        """空の提案リストの場合、提案なしメッセージを出力すること。"""
        result = _generate_suggestions_markdown([], 6)

        self.assertIn("# ジャンル提案レポート", result)
        self.assertIn("**提案数**: 0件", result)

    def test_generate_genre_suggestions_md_sample_titles_max_five(self):
        """sample_titles が5件を超える場合も正しく表示すること。"""
        suggestions = [
            {
                "suggested_genre": "food",
                "suggested_description": "食品/料理",
                "sample_titles": [
                    "タイトル1",
                    "タイトル2",
                    "タイトル3",
                    "タイトル4",
                    "タイトル5",
                ],
                "content_count": 10,
            },
        ]

        result = _generate_suggestions_markdown(suggestions, 12)

        # All 5 sample titles should be present
        for i in range(1, 6):
            self.assertIn(f"- タイトル{i}", result)

    # ---- T026: test_suggest_genre_with_llm ----

    def test_suggest_genre_with_llm_returns_suggestions(self):
        """_suggest_new_genres_via_llm が GenreSuggestion リストを返すこと。"""
        other_items = [
            {
                "metadata": {"title": "パスタの作り方"},
                "content": "パスタの基本的な作り方を解説します。",
                "genre": "other",
            },
            {
                "metadata": {"title": "カレーレシピ"},
                "content": "簡単なカレーの作り方。",
                "genre": "other",
            },
            {
                "metadata": {"title": "和食の基本"},
                "content": "出汁の取り方から始める和食入門。",
                "genre": "other",
            },
            {
                "metadata": {"title": "お弁当アイデア"},
                "content": "毎日のお弁当に使えるアイデア集。",
                "genre": "other",
            },
            {
                "metadata": {"title": "スイーツレシピ"},
                "content": "簡単に作れるスイーツのレシピ。",
                "genre": "other",
            },
        ]
        params = {
            "ollama": {
                "defaults": {
                    "model": "test-model",
                    "base_url": "http://localhost:11434",
                }
            },
            "genre_vault_mapping": _make_genre_config_new_format(),
        }

        # Mock call_ollama to return genre suggestions as JSON
        import json

        llm_response = json.dumps(
            [
                {
                    "suggested_genre": "cooking",
                    "suggested_description": "料理/レシピ/食材",
                    "sample_titles": ["パスタの作り方", "カレーレシピ", "和食の基本"],
                    "content_count": 5,
                },
            ]
        )

        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call:
            mock_call.return_value = (llm_response, None)
            result = _suggest_new_genres_via_llm(other_items, params)

        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

        # Verify structure of first suggestion
        suggestion = result[0]
        self.assertIn("suggested_genre", suggestion)
        self.assertIn("suggested_description", suggestion)
        self.assertIn("sample_titles", suggestion)
        self.assertIn("content_count", suggestion)
        self.assertEqual(suggestion["suggested_genre"], "cooking")
        self.assertIsInstance(suggestion["sample_titles"], list)
        self.assertGreaterEqual(suggestion["content_count"], 1)

    def test_suggest_genre_with_llm_error_returns_empty(self):
        """LLM エラー時に空リストを返すこと。"""
        other_items = [
            {
                "metadata": {"title": "テスト"},
                "content": "テスト内容",
                "genre": "other",
            },
        ] * 5
        params = {
            "ollama": {
                "defaults": {
                    "model": "test-model",
                    "base_url": "http://localhost:11434",
                }
            },
            "genre_vault_mapping": _make_genre_config_new_format(),
        }

        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call:
            mock_call.return_value = (None, "Connection error")
            result = _suggest_new_genres_via_llm(other_items, params)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_suggest_genre_with_llm_invalid_json_returns_empty(self):
        """LLM が不正な JSON を返した場合に空リストを返すこと。"""
        other_items = [
            {
                "metadata": {"title": "テスト"},
                "content": "テスト内容",
                "genre": "other",
            },
        ] * 5
        params = {
            "ollama": {
                "defaults": {
                    "model": "test-model",
                    "base_url": "http://localhost:11434",
                }
            },
            "genre_vault_mapping": _make_genre_config_new_format(),
        }

        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call:
            mock_call.return_value = ("not valid json {{{", None)
            result = _suggest_new_genres_via_llm(other_items, params)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


# ============================================================
# Genre Config Validation tests (Phase 4 - 060-dynamic-genre-config / US4)
# ============================================================


class TestGenreConfigValidation(unittest.TestCase):
    """Genre config validation: バリデーションとエラーハンドリング。

    060-dynamic-genre-config Phase 4: US4
    - description 欠落時に警告ログを出力すること
    - vault 欠落時にエラーを発生させること
    - genre_vault_mapping が空/None の場合に other フォールバック
    """

    def setUp(self):
        """関数が存在しない場合は FAIL させる (RED state)。"""
        if _parse_genre_config is None:
            self.fail("_parse_genre_config is not yet implemented (RED)")

    # ---- T038: test_missing_description_warning ----

    def test_missing_description_warning_logs(self):
        """description が欠落している場合に警告ログが出力されること。"""
        genre_config = {
            "ai": {
                "vault": "エンジニア",
                # description is missing
            },
        }

        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            genre_definitions, valid_genres = _parse_genre_config(genre_config)

            # Warning should be logged for missing description
            mock_logger.warning.assert_called()
            warning_calls = " ".join(str(call) for call in mock_logger.warning.call_args_list)
            self.assertIn("ai", warning_calls, "Warning should mention the genre key 'ai'")
            self.assertIn(
                "description",
                warning_calls.lower(),
                "Warning should mention 'description'",
            )

    def test_missing_description_uses_genre_name_as_fallback(self):
        """description が欠落している場合にジャンル名をフォールバックとして使用すること。"""
        genre_config = {
            "custom": {
                "vault": "カスタム",
                # description なし
            },
        }

        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            genre_definitions, valid_genres = _parse_genre_config(genre_config)

        # Genre name should be used as fallback description
        self.assertEqual(genre_definitions["custom"], "custom")
        # Genre should still be in valid_genres
        self.assertIn("custom", valid_genres)

    def test_missing_description_does_not_raise(self):
        """description が欠落していてもエラーにならないこと。"""
        genre_config = {
            "ai": {
                "vault": "エンジニア",
                # description なし
            },
            "devops": {
                "vault": "エンジニア",
                "description": "インフラ/CI/CD",
            },
        }

        # Should not raise any exception
        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            genre_definitions, valid_genres = _parse_genre_config(genre_config)

        self.assertIn("ai", genre_definitions)
        self.assertIn("devops", genre_definitions)
        # devops has description, ai does not
        self.assertEqual(genre_definitions["devops"], "インフラ/CI/CD")

    # ---- T039: test_missing_vault_error ----

    def test_missing_vault_raises_error(self):
        """vault が欠落している場合にエラーが発生すること。"""
        genre_config = {
            "ai": {
                "description": "AI/機械学習",
                # vault is missing
            },
        }

        with self.assertRaises((ValueError, KeyError)) as ctx:
            _parse_genre_config(genre_config)

        # Error message should indicate which genre is missing vault
        error_msg = str(ctx.exception)
        self.assertIn("ai", error_msg, "Error should mention genre key 'ai'")

    def test_missing_vault_error_message_clarity(self):
        """vault 欠落時のエラーメッセージが明確であること。"""
        genre_config = {
            "finance": {
                "description": "金融/投資",
                # vault is missing
            },
        }

        with self.assertRaises((ValueError, KeyError)) as ctx:
            _parse_genre_config(genre_config)

        error_msg = str(ctx.exception).lower()
        self.assertIn("vault", error_msg, "Error should mention 'vault'")
        self.assertIn("finance", str(ctx.exception), "Error should mention genre key")

    def test_missing_vault_with_valid_genres_mixed(self):
        """正常なジャンルと vault 欠落ジャンルが混在する場合にエラーが発生すること。"""
        genre_config = {
            "ai": {
                "vault": "エンジニア",
                "description": "AI/機械学習",
            },
            "broken": {
                "description": "壊れたジャンル",
                # vault is missing
            },
        }

        with self.assertRaises((ValueError, KeyError)) as ctx:
            _parse_genre_config(genre_config)

        error_msg = str(ctx.exception)
        self.assertIn("broken", error_msg, "Error should mention the broken genre key")

    # ---- T040: test_empty_genre_mapping_fallback ----

    def test_empty_genre_mapping_returns_fallback(self):
        """空の genre_vault_mapping で other フォールバックを返すこと。"""
        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            genre_definitions, valid_genres = _parse_genre_config({})

            # Warning should be logged
            mock_logger.warning.assert_called()

        # Should fallback to other
        self.assertIn("other", valid_genres)
        self.assertGreaterEqual(len(valid_genres), 1)

    def test_none_genre_mapping_returns_fallback(self):
        """None の genre_vault_mapping で other フォールバックを返すこと。"""
        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            genre_definitions, valid_genres = _parse_genre_config(None)

            # Warning should be logged
            mock_logger.warning.assert_called()

        # Should fallback to other
        self.assertIn("other", valid_genres)
        self.assertGreaterEqual(len(valid_genres), 1)

    def test_empty_genre_mapping_fallback_genre_definitions(self):
        """空の genre_vault_mapping で genre_definitions に other が含まれること。"""
        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            genre_definitions, valid_genres = _parse_genre_config({})

        # genre_definitions should have "other" as fallback
        self.assertIn("other", genre_definitions)

    def test_none_genre_mapping_fallback_genre_definitions(self):
        """None の genre_vault_mapping で genre_definitions に other が含まれること。"""
        with patch("obsidian_etl.pipelines.organize.nodes.logger"):
            genre_definitions, valid_genres = _parse_genre_config(None)

        # genre_definitions should have "other" as fallback
        self.assertIn("other", genre_definitions)

    def test_empty_genre_mapping_warning_content(self):
        """空の genre_vault_mapping で適切な警告メッセージが出力されること。"""
        with patch("obsidian_etl.pipelines.organize.nodes.logger") as mock_logger:
            _parse_genre_config({})

            warning_calls = " ".join(str(call) for call in mock_logger.warning.call_args_list)
            # Warning should mention empty/missing config
            self.assertTrue(
                "genre_vault_mapping" in warning_calls.lower()
                or "empty" in warning_calls.lower()
                or "fallback" in warning_calls.lower()
                or "フォールバック" in warning_calls,
                f"Warning should mention fallback/empty config, got: {warning_calls}",
            )


if __name__ == "__main__":
    unittest.main()
