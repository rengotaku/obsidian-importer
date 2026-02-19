"""Tests for Organize pipeline nodes.

Tests verify:
- Keyword-based genre classification (engineer, business, economy, daily, other)
- Default genre fallback when no keyword matches
- Frontmatter normalization (normalized=True, clean unnecessary fields)
- Content cleanup (excess blank lines, formatting)
- Topic extraction from content (LLM-based, lowercase normalized)
- Frontmatter embedding of genre, topic, summary (no file I/O)
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from obsidian_etl.pipelines.organize.nodes import (
    classify_genre,
    clean_content,
    embed_frontmatter_fields,
    extract_topic,
    normalize_frontmatter,
)


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
    }


def _make_partitioned_input(items: dict[str, dict]) -> dict[str, callable]:
    """Create PartitionedDataset-style input (dict of callables)."""
    return {key: (lambda v=val: v) for key, val in items.items()}


# ============================================================
# classify_genre node tests
# ============================================================


class TestClassifyGenre(unittest.TestCase):
    """classify_genre: keyword-based genre detection from tags and content."""

    def test_classify_genre_engineer(self):
        """エンジニア関連のタグ/コンテンツが 'engineer' に分類されること。"""
        item = _make_markdown_item(
            title="Python プログラミング入門",
            tags=["Python", "プログラミング", "入門"],
        )
        partitioned_input = _make_partitioned_input({"item-eng": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)

        classified_item = list(result.values())[0]
        self.assertIn("genre", classified_item)
        self.assertEqual(classified_item["genre"], "engineer")

    def test_classify_genre_business(self):
        """ビジネス関連のタグ/コンテンツが 'business' に分類されること。"""
        item = _make_markdown_item(
            title="マネジメントの基本",
            tags=["ビジネス", "マネジメント"],
        )
        partitioned_input = _make_partitioned_input({"item-biz": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "business")

    def test_classify_genre_economy(self):
        """経済関連のタグ/コンテンツが 'economy' に分類されること。"""
        item = _make_markdown_item(
            title="投資戦略の分析",
            tags=["投資", "金融"],
        )
        partitioned_input = _make_partitioned_input({"item-eco": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "economy")

    def test_classify_genre_daily(self):
        """日常関連のタグ/コンテンツが 'daily' に分類されること。"""
        item = _make_markdown_item(
            title="週末の趣味活動",
            tags=["趣味", "日常"],
        )
        partitioned_input = _make_partitioned_input({"item-daily": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "daily")

    def test_classify_genre_from_content(self):
        """タグにキーワードがなくても、コンテンツからジャンルが検出されること。"""
        content = (
            "---\n"
            "title: データベース設計\n"
            "created: 2026-01-15\n"
            "tags:\n"
            "  - 設計\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "データベースの正規化について解説する。\n"
        )
        item = _make_markdown_item(
            title="データベース設計",
            tags=["設計"],
            content=content,
        )
        partitioned_input = _make_partitioned_input({"item-content": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "engineer")

    def test_classify_genre_ai(self):
        """AI関連のタグ/コンテンツが 'ai' に分類されること。"""
        item = _make_markdown_item(
            title="ChatGPT を使った文章生成",
            tags=["ChatGPT", "LLM", "生成AI"],
        )
        partitioned_input = _make_partitioned_input({"item-ai": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "ai")

    def test_classify_genre_devops(self):
        """DevOps関連のタグ/コンテンツが 'devops' に分類されること。"""
        item = _make_markdown_item(
            title="Docker コンテナの運用",
            tags=["Docker", "コンテナ", "インフラ"],
        )
        partitioned_input = _make_partitioned_input({"item-devops": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "devops")

    def test_classify_genre_lifestyle(self):
        """ライフスタイル関連のタグ/コンテンツが 'lifestyle' に分類されること。"""
        item = _make_markdown_item(
            title="電子レンジの選び方",
            tags=["家電", "電子レンジ"],
        )
        partitioned_input = _make_partitioned_input({"item-lifestyle": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "lifestyle")

    def test_classify_genre_parenting(self):
        """子育て関連のタグ/コンテンツが 'parenting' に分類されること。"""
        item = _make_markdown_item(
            title="赤ちゃんの離乳食",
            tags=["子育て", "育児", "赤ちゃん"],
        )
        partitioned_input = _make_partitioned_input({"item-parenting": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "parenting")

    def test_classify_genre_travel(self):
        """旅行関連のタグ/コンテンツが 'travel' に分類されること。"""
        item = _make_markdown_item(
            title="宮崎への家族旅行",
            tags=["旅行", "観光"],
        )
        partitioned_input = _make_partitioned_input({"item-travel": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "travel")

    def test_classify_genre_health(self):
        """健康関連のタグ/コンテンツが 'health' に分類されること。"""
        item = _make_markdown_item(
            title="フィットネスと健康管理",
            tags=["健康", "フィットネス", "運動"],
        )
        partitioned_input = _make_partitioned_input({"item-health": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "health")

    def test_classify_genre_priority_ai_over_engineer(self):
        """AI と engineer の両方にマッチする場合、ai が優先されること。

        「Claude でプログラミング」は ai キーワード (Claude) と
        engineer キーワード (プログラミング) の両方にマッチするが、
        優先順位により ai に分類される。
        """
        item = _make_markdown_item(
            title="Claude でプログラミング",
            tags=["Claude", "プログラミング"],
        )
        partitioned_input = _make_partitioned_input({"item-ai-eng": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "ai")

    def test_classify_genre_priority_devops_over_engineer(self):
        """DevOps と engineer の両方にマッチする場合、devops が優先されること。

        「AWS でのAPI設計」は devops キーワード (AWS) と
        engineer キーワード (API) の両方にマッチするが、
        優先順位により devops に分類される。
        """
        item = _make_markdown_item(
            title="AWS でのAPI設計",
            tags=["AWS", "API"],
        )
        partitioned_input = _make_partitioned_input({"item-devops-eng": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "devops")

    def test_classify_genre_multiple_items(self):
        """複数アイテムがそれぞれ正しくジャンル分類されること。"""
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

        result = classify_genre(partitioned_input, params)

        self.assertEqual(len(result), 2)
        genres = {v["item_id"]: v["genre"] for v in result.values()}
        self.assertEqual(genres["eng"], "engineer")
        self.assertEqual(genres["biz"], "business")


class TestClassifyGenreDefault(unittest.TestCase):
    """classify_genre: no keyword match -> 'other'."""

    def test_classify_genre_default_other(self):
        """どのキーワードにもマッチしない場合、'other' に分類されること。"""
        item = _make_markdown_item(
            title="哲学的な考察",
            tags=["哲学", "思想"],
        )
        # Content also has no matching keywords
        item["content"] = (
            "---\n"
            "title: 哲学的な考察\n"
            "tags:\n"
            "  - 哲学\n"
            "normalized: true\n"
            "---\n"
            "\n"
            "存在と時間について考える。\n"
        )
        partitioned_input = _make_partitioned_input({"item-other": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "other")

    def test_classify_genre_empty_tags(self):
        """タグが空でコンテンツにもキーワードがない場合、'other' になること。"""
        item = _make_markdown_item(
            title="無題",
            tags=[],
        )
        item["content"] = (
            "---\ntitle: 無題\ntags: []\nnormalized: true\n---\n\n特に分類できない内容。\n"
        )
        partitioned_input = _make_partitioned_input({"item-empty-tags": item})
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "other")

    def test_classify_genre_no_genre_keywords_param(self):
        """genre_keywords パラメータが空の場合、全て 'other' になること。"""
        item = _make_markdown_item(
            title="Python プログラミング",
            tags=["Python", "プログラミング"],
        )
        partitioned_input = _make_partitioned_input({"item-no-kw": item})
        params = _make_organize_params()
        params["genre_keywords"] = {}

        result = classify_genre(partitioned_input, params)

        classified_item = list(result.values())[0]
        self.assertEqual(classified_item["genre"], "other")


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
# extract_topic node tests (Phase 2 - 047-e2e-full-pipeline)
# ============================================================


class TestExtractTopic(unittest.TestCase):
    """extract_topic: LLM-based topic extraction with lowercase normalization."""

    def test_extract_topic_normalizes_to_lowercase(self):
        """topic が小文字に正規化されること。

        LLM が "AWS" を返した場合、"aws" に正規化される。
        """
        item = _make_markdown_item(
            title="AWSのLambda関数について",
            tags=["AWS", "Lambda", "serverless"],
        )
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-aws": item})
        params = _make_organize_params()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        # Mock LLM to return uppercase topic
        with patch("obsidian_etl.pipelines.organize.nodes._extract_topic_via_llm") as mock_llm:
            mock_llm.return_value = "AWS"
            result = extract_topic(partitioned_input, params)

        topic_item = list(result.values())[0]
        self.assertIn("topic", topic_item)
        self.assertEqual(topic_item["topic"], "aws")

    def test_extract_topic_preserves_spaces(self):
        """topic のスペースが保持されること。

        "React Native" -> "react native" (スペース保持、小文字化)
        """
        item = _make_markdown_item(
            title="React Native開発入門",
            tags=["React Native", "モバイル開発"],
        )
        item["genre"] = "engineer"
        partitioned_input = _make_partitioned_input({"item-rn": item})
        params = _make_organize_params()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        # Mock LLM to return topic with spaces
        with patch("obsidian_etl.pipelines.organize.nodes._extract_topic_via_llm") as mock_llm:
            mock_llm.return_value = "React Native"
            result = extract_topic(partitioned_input, params)

        topic_item = list(result.values())[0]
        self.assertIn("topic", topic_item)
        self.assertEqual(topic_item["topic"], "react native")

    def test_extract_topic_empty_on_failure(self):
        """抽出失敗時は空文字が設定されること。

        LLM が None や空文字を返した場合、topic は空文字になる。
        """
        item = _make_markdown_item(
            title="雑多なメモ",
            tags=["メモ"],
        )
        item["genre"] = "other"
        partitioned_input = _make_partitioned_input({"item-empty": item})
        params = _make_organize_params()
        params["ollama"] = {"model": "test-model", "base_url": "http://localhost:11434"}

        # Mock LLM to return empty (extraction failure)
        with patch("obsidian_etl.pipelines.organize.nodes._extract_topic_via_llm") as mock_llm:
            mock_llm.return_value = None
            result = extract_topic(partitioned_input, params)

        topic_item = list(result.values())[0]
        self.assertIn("topic", topic_item)
        self.assertEqual(topic_item["topic"], "")


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
# Idempotent organize tests (Phase 6 - US2)
# ============================================================


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


class TestIdempotentOrganize(unittest.TestCase):
    """classify_genre: existing output partitions -> skip items, no re-classify."""

    def test_idempotent_organize_skips_existing(self):
        """existing_output に存在するアイテムはスキップされ、新規のみ分類されること。"""
        items = {
            "item-a": _make_markdown_item(
                item_id="a",
                title="API設計",
                tags=["API", "設計"],
            ),
            "item-b": _make_markdown_item(
                item_id="b",
                title="マネジメント入門",
                tags=["マネジメント"],
            ),
            "item-c": _make_markdown_item(
                item_id="c",
                title="投資戦略",
                tags=["投資"],
            ),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()

        # item-a and item-b already classified
        existing_output = {
            "item-a": lambda: {**items["item-a"], "genre": "engineer"},
            "item-b": lambda: {**items["item-b"], "genre": "business"},
        }

        result = classify_genre(partitioned_input, params, existing_output=existing_output)

        # Only item-c should be returned (new item)
        self.assertEqual(len(result), 1)
        self.assertIn("item-c", result)
        self.assertEqual(result["item-c"]["genre"], "economy")

    def test_idempotent_organize_all_existing_returns_empty(self):
        """全アイテムが既に分類済みの場合、空 dict が返ること。"""
        items = {
            "item-a": _make_markdown_item(item_id="a", tags=["API"]),
            "item-b": _make_markdown_item(item_id="b", tags=["ビジネス"]),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()

        existing_output = {
            "item-a": lambda: {**items["item-a"], "genre": "engineer"},
            "item-b": lambda: {**items["item-b"], "genre": "business"},
        }

        result = classify_genre(partitioned_input, params, existing_output=existing_output)
        self.assertEqual(len(result), 0)

    def test_idempotent_organize_no_existing_output_processes_all(self):
        """existing_output 引数なしで全アイテムが分類されること（後方互換性）。"""
        items = {
            "item-a": _make_markdown_item(item_id="a", tags=["API"]),
            "item-b": _make_markdown_item(item_id="b", tags=["ビジネス"]),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_organize_params()

        result = classify_genre(partitioned_input, params)

        self.assertEqual(len(result), 2)


# ============================================================
# extract_topic Ollama config tests (Phase 4 - 051-ollama-params-config)
# ============================================================


class TestExtractTopicUsesOllamaConfig(unittest.TestCase):
    """extract_topic: verify integration with get_ollama_config.

    These tests verify that _extract_topic_via_llm uses get_ollama_config
    to retrieve function-specific parameters and passes them correctly
    to the Ollama API.
    """

    def test_extract_topic_uses_config(self):
        """_extract_topic_via_llm が get_ollama_config を呼び出すこと。

        Verify that _extract_topic_via_llm calls get_ollama_config(params, "extract_topic")
        to retrieve the configuration.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_via_llm

        content = "## 要約\n\nPythonの非同期処理について解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "timeout": 120},
                "functions": {
                    "extract_topic": {"model": "llama3.2:3b", "num_predict": 64, "timeout": 30}
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
                num_predict=64,
            )

            # Also mock the actual API call to avoid network calls
            with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
                mock_call_ollama.return_value = ("python", None)
                _extract_topic_via_llm(content, params)

            # Verify get_ollama_config was called with correct arguments
            mock_get_config.assert_called_once_with(params, "extract_topic")

    def test_extract_topic_uses_correct_model(self):
        """extract_topic が設定されたモデルを使用すること。

        Verify that the model from ollama.functions.extract_topic is used
        in the API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_via_llm

        content = "## 要約\n\nAWSのLambda関数について解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b"},
                "functions": {"extract_topic": {"model": "llama3.2:3b"}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = ("aws", None)
            _extract_topic_via_llm(content, params)

            # Verify call_ollama was called with the correct model
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that model argument is "llama3.2:3b" (from functions.extract_topic)
            self.assertEqual(call_kwargs.kwargs.get("model"), "llama3.2:3b")

    def test_extract_topic_uses_correct_timeout(self):
        """extract_topic が設定されたタイムアウトを使用すること。

        Verify that the timeout from ollama.functions.extract_topic is used
        in the API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_via_llm

        content = "## 要約\n\nReact Nativeでモバイルアプリを開発します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "timeout": 120},
                "functions": {"extract_topic": {"timeout": 30}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = ("mobile development", None)
            _extract_topic_via_llm(content, params)

            # Verify call_ollama was called with the correct timeout
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that timeout argument is 30 (from functions.extract_topic)
            self.assertEqual(call_kwargs.kwargs.get("timeout"), 30)

    def test_extract_topic_num_predict_applied(self):
        """extract_topic が num_predict を Ollama API に渡すこと。

        Verify that num_predict from ollama.functions.extract_topic is passed
        to the Ollama API call.
        """
        from obsidian_etl.pipelines.organize.nodes import _extract_topic_via_llm

        content = "## 要約\n\nDockerコンテナについて解説します。"
        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b", "num_predict": -1},
                "functions": {"extract_topic": {"num_predict": 64}},
            }
        }

        # Mock call_ollama to capture the arguments
        with patch("obsidian_etl.pipelines.organize.nodes.call_ollama") as mock_call_ollama:
            mock_call_ollama.return_value = ("docker", None)
            _extract_topic_via_llm(content, params)

            # Verify call_ollama was called with the correct num_predict
            mock_call_ollama.assert_called_once()
            call_kwargs = mock_call_ollama.call_args
            # Check that num_predict argument is 64 (from functions.extract_topic)
            self.assertEqual(call_kwargs.kwargs.get("num_predict"), 64)


if __name__ == "__main__":
    unittest.main()
