# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 4: パイプライン変更: Vault 書き込み廃止
- FAIL テスト数: 8
- テストファイル: `tests/pipelines/organize/test_nodes.py`

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| tests/pipelines/organize/test_nodes.py | TestExtractTopic | test_extract_topic_normalizes_to_lowercase | LLM が "AWS" を返した場合、"aws" に正規化される |
| tests/pipelines/organize/test_nodes.py | TestExtractTopic | test_extract_topic_preserves_spaces | "React Native" → "react native" (スペース保持、小文字化) |
| tests/pipelines/organize/test_nodes.py | TestExtractTopic | test_extract_topic_empty_on_failure | LLM が None や空文字を返した場合、topic は空文字 |
| tests/pipelines/organize/test_nodes.py | TestEmbedFrontmatterFields | test_embed_frontmatter_fields_adds_genre | genre が frontmatter に追加される |
| tests/pipelines/organize/test_nodes.py | TestEmbedFrontmatterFields | test_embed_frontmatter_fields_adds_topic | topic が frontmatter に追加される |
| tests/pipelines/organize/test_nodes.py | TestEmbedFrontmatterFields | test_embed_frontmatter_fields_adds_empty_topic | 空の topic が frontmatter に追加される (空許容) |
| tests/pipelines/organize/test_nodes.py | TestEmbedFrontmatterFields | test_embed_frontmatter_fields_adds_summary | summary が frontmatter に追加される |
| tests/pipelines/organize/test_nodes.py | TestEmbedFrontmatterFields | test_embed_frontmatter_fields_no_file_write | ファイルシステムへの書き込みが発生しない |

## 実装ヒント

### extract_topic

- `src/obsidian_etl/pipelines/organize/nodes.py` に `extract_topic(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]` を実装
- `_extract_topic_via_llm(content: str, params: dict) -> str | None` ヘルパー関数を実装
- topic 正規化: `topic.lower() if topic else ""`
- スペースは保持（AWS → aws, React Native → react native）
- LLM 抽出失敗時は空文字

### embed_frontmatter_fields

- `src/obsidian_etl/pipelines/organize/nodes.py` に `embed_frontmatter_fields(partitioned_input: dict[str, Callable], params: dict) -> dict[str, str]` を実装
- `_embed_fields_in_frontmatter(content: str, genre: str, topic: str, summary: str) -> str` ヘルパー関数を実装
- frontmatter に `genre`, `topic`, `summary` を追加
- ファイル I/O なし（メモリ上で処理）
- 戻り値は `dict[str, str]` (output_filename -> content)

### テストで使用するモック

```python
from unittest.mock import patch

with patch("obsidian_etl.pipelines.organize.nodes._extract_topic_via_llm") as mock_llm:
    mock_llm.return_value = "AWS"  # or None for failure
    result = extract_topic(partitioned_input, params)
```

## FAIL 出力例

```
$ .venv/bin/python -m unittest tests.pipelines.organize.test_nodes.TestExtractTopic tests.pipelines.organize.test_nodes.TestEmbedFrontmatterFields 2>&1

EE
======================================================================
ERROR: test_nodes (unittest.loader._FailedTest.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_nodes
Traceback (most recent call last):
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
  File "/data/projects/obsidian-importer/tests/pipelines/organize/test_nodes.py", line 26, in <module>
    from obsidian_etl.pipelines.organize.nodes import (
    ...<7 lines>...
    )
ImportError: cannot import name 'embed_frontmatter_fields' from 'obsidian_etl.pipelines.organize.nodes' (/data/projects/obsidian-importer/src/obsidian_etl/pipelines/organize/nodes.py)

----------------------------------------------------------------------
Ran 2 tests in 0.000s

FAILED (errors=2)
```

## テストコード

### TestExtractTopic

```python
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
```

### TestEmbedFrontmatterFields

```python
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
```

## 次ステップ

phase-executor が「実装 (GREEN)」→「検証」を実行:

1. `src/obsidian_etl/pipelines/organize/nodes.py` に `extract_topic` と `embed_frontmatter_fields` を実装
2. `_extract_topic_via_llm` と `_embed_fields_in_frontmatter` ヘルパー関数を実装
3. `make test` で新規テストが PASS することを確認
4. 既存テストが引き続き PASS することを確認（後方互換性）
