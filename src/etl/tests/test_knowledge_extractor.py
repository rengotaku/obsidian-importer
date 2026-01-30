"""Unit tests for KnowledgeExtractor with markdown response parsing.

Tests for:
- T010: extract() uses parse_markdown_response to generate KnowledgeDocument from markdown
- T011: translate_summary() parses markdown format response correctly
- T023: Integration test: markdown response -> extract() -> to_markdown() backward compatibility
"""

import unittest
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

from src.etl.utils.knowledge_extractor import (
    ExtractionResult,
    KnowledgeDocument,
    KnowledgeExtractor,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class FakeMessage:
    """テスト用メッセージ"""

    content: str
    _role: str = "user"

    @property
    def role(self) -> str:
        return self._role


@dataclass
class FakeConversation:
    """テスト用会話データ"""

    title: str = "テスト会話"
    created_at: str = "2026-01-30T10:00:00"
    messages: list = field(default_factory=list)
    summary: str = ""
    _id: str = "conv-001"
    _provider: str = "claude"

    @property
    def id(self) -> str:
        return self._id

    @property
    def provider(self) -> str:
        return self._provider


def make_conversation(
    title: str = "テスト会話",
    messages: list[tuple[str, str]] | None = None,
    summary: str = "",
    created_at: str = "2026-01-30T10:00:00",
) -> FakeConversation:
    """テスト用会話を作成するヘルパー"""
    if messages is None:
        messages = [
            ("user", "Pythonのデコレータについて教えてください"),
            ("assistant", "デコレータは関数を受け取り拡張する高階関数です。"),
            ("user", "具体例を見せてください"),
            ("assistant", "@functools.wraps を使った例を示します。"),
        ]
    msg_objects = [FakeMessage(content=content, _role=role) for role, content in messages]
    return FakeConversation(
        title=title,
        created_at=created_at,
        messages=msg_objects,
        summary=summary,
    )


# =============================================================================
# T010: extract() with markdown response
# =============================================================================


class TestKnowledgeExtractorExtractMarkdown(unittest.TestCase):
    """T010: extract() が parse_markdown_response を使用し、
    マークダウンレスポンスから KnowledgeDocument を生成することを確認"""

    def setUp(self):
        """KnowledgeExtractor を初期化"""
        self.extractor = KnowledgeExtractor()

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_with_markdown_response_returns_success(self, mock_call_ollama):
        """マークダウンレスポンスから正常に KnowledgeDocument が生成される"""
        markdown_response = (
            "# Pythonデコレータパターン\n"
            "\n"
            "## 要約\n"
            "Pythonのデコレータを使った関数拡張について解説。\n"
            "\n"
            "## 内容\n"
            "デコレータは高階関数の一種で、関数を受け取り拡張された関数を返します。\n"
            "\n"
            "### 基本例\n"
            "```python\n"
            "@my_decorator\n"
            "def hello():\n"
            "    pass\n"
            "```\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation()
        result = self.extractor.extract(conversation)

        self.assertIsInstance(result, ExtractionResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertIsInstance(result.document, KnowledgeDocument)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_markdown_populates_summary(self, mock_call_ollama):
        """マークダウンの ## 要約 セクションが document.summary に入る"""
        markdown_response = (
            "# タイトル\n"
            "\n"
            "## 要約\n"
            "デコレータパターンの基本的な使い方。\n"
            "\n"
            "## 内容\n"
            "本文テキスト。\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="")
        result = self.extractor.extract(conversation)

        self.assertTrue(result.success)
        self.assertEqual(result.document.summary, "デコレータパターンの基本的な使い方。")

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_markdown_populates_summary_content(self, mock_call_ollama):
        """マークダウンの ## 内容 セクションが document.summary_content に入る"""
        markdown_response = (
            "# タイトル\n"
            "\n"
            "## 要約\n"
            "要約テキスト。\n"
            "\n"
            "## 内容\n"
            "詳細な内容がここに入ります。コードも含みます。\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="")
        result = self.extractor.extract(conversation)

        self.assertTrue(result.success)
        self.assertIn("詳細な内容", result.document.summary_content)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_uses_parse_markdown_not_json(self, mock_call_ollama):
        """extract() が parse_markdown_response を呼び出す（parse_json_response ではない）"""
        markdown_response = "# テスト\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation()

        with patch("src.etl.utils.knowledge_extractor.parse_markdown_response") as mock_parse_md:
            mock_parse_md.return_value = (
                {"title": "テスト", "summary": "要約。", "summary_content": "内容。"},
                None,
            )
            result = self.extractor.extract(conversation)
            mock_parse_md.assert_called_once()

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_markdown_parse_error_returns_failure(self, mock_call_ollama):
        """パースエラーの場合、success=False の ExtractionResult が返る"""
        mock_call_ollama.return_value = ("", None)

        conversation = make_conversation()
        result = self.extractor.extract(conversation)

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_extract_preserves_conversation_metadata(self, mock_call_ollama):
        """抽出結果に会話のメタデータ（created, provider, id）が保持される"""
        markdown_response = "# タイトル\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(created_at="2026-01-30T10:00:00")
        result = self.extractor.extract(conversation)

        self.assertTrue(result.success)
        self.assertEqual(result.document.created, "2026-01-30")
        self.assertEqual(result.document.source_provider, "claude")
        self.assertEqual(result.document.source_conversation, "conv-001")


# =============================================================================
# T011: translate_summary() with markdown response
# =============================================================================


class TestKnowledgeExtractorTranslateSummaryMarkdown(unittest.TestCase):
    """T011: translate_summary() がマークダウン形式のレスポンスを正しくパースする"""

    def setUp(self):
        """KnowledgeExtractor を初期化"""
        self.extractor = KnowledgeExtractor()

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_parses_markdown_response(self, mock_call_ollama):
        """マークダウン形式の翻訳レスポンスから summary が正しく抽出される"""
        markdown_response = "## 要約\nPythonデコレータの基本的なパターンについての議論。\n"
        mock_call_ollama.return_value = (markdown_response, None)

        result, error = self.extractor.translate_summary(
            "Discussion about basic Python decorator patterns."
        )

        self.assertIsNone(error)
        self.assertEqual(result, "Pythonデコレータの基本的なパターンについての議論。")

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_uses_parse_markdown(self, mock_call_ollama):
        """translate_summary() が parse_markdown_response を使用する"""
        markdown_response = "## 要約\n翻訳テキスト。\n"
        mock_call_ollama.return_value = (markdown_response, None)

        with patch("src.etl.utils.knowledge_extractor.parse_markdown_response") as mock_parse_md:
            mock_parse_md.return_value = ({"summary": "翻訳テキスト。"}, None)
            result, error = self.extractor.translate_summary("English summary text.")
            mock_parse_md.assert_called_once()

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_returns_error_on_parse_failure(self, mock_call_ollama):
        """パースエラー時にエラーメッセージが返される"""
        mock_call_ollama.return_value = ("", None)

        result, error = self.extractor.translate_summary("Some English text.")

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_returns_error_on_api_failure(self, mock_call_ollama):
        """API エラー時にエラーメッセージが返される"""
        mock_call_ollama.return_value = ("", "接続エラー: Connection refused")

        result, error = self.extractor.translate_summary("Some English text.")

        self.assertIsNone(result)
        self.assertIn("接続エラー", error)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_with_multiline_markdown(self, mock_call_ollama):
        """複数行の翻訳結果が正しく抽出される"""
        markdown_response = "## 要約\nDockerコンテナ化の基本。マルチステージビルドの利点も解説。\n"
        mock_call_ollama.return_value = (markdown_response, None)

        result, error = self.extractor.translate_summary(
            "Basics of Docker containerization. Also explains multi-stage build benefits."
        )

        self.assertIsNone(error)
        self.assertIn("Docker", result)


# =============================================================================
# T023: Integration test - markdown response -> extract() -> to_markdown()
# =============================================================================


class TestMarkdownResponseToMarkdownOutput(unittest.TestCase):
    """T023: マークダウンレスポンスを受け取った KnowledgeExtractor が
    to_markdown() で従来と同じフォーマットの Markdown ファイルを生成することを確認。

    End-to-end フロー:
    1. Mock LLM がマークダウンレスポンスを返す
    2. KnowledgeExtractor.extract() が parse_markdown_response() で処理
    3. KnowledgeDocument.to_markdown() が正しい出力フォーマットを生成
    """

    def setUp(self):
        """KnowledgeExtractor を初期化"""
        self.extractor = KnowledgeExtractor(fetch_titles=False)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_has_valid_frontmatter(self, mock_call_ollama):
        """to_markdown() 出力が正しい YAML frontmatter を含む（title, summary, created）"""
        markdown_response = (
            "# Pythonデコレータの活用法\n"
            "\n"
            "## 要約\n"
            "Pythonデコレータを使った関数拡張の基本パターン。\n"
            "\n"
            "## 内容\n"
            "デコレータは高階関数の一種です。\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(
            title="テスト会話",
            created_at="2026-01-30T10:00:00",
        )
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # frontmatter が --- で囲まれている
        self.assertTrue(output.startswith("---\n"))
        self.assertIn("\n---\n", output)

        # frontmatter フィールド検証
        lines = output.split("\n")
        frontmatter_end = lines.index("---", 1)
        frontmatter_lines = lines[1:frontmatter_end]
        frontmatter_text = "\n".join(frontmatter_lines)

        self.assertIn("title: テスト会話", frontmatter_text)
        self.assertIn(
            "summary: Pythonデコレータを使った関数拡張の基本パターン。",
            frontmatter_text,
        )
        self.assertIn("created: 2026-01-30", frontmatter_text)
        self.assertIn("source_provider: claude", frontmatter_text)
        self.assertIn("source_conversation: conv-001", frontmatter_text)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_heading_normalization(self, mock_call_ollama):
        """to_markdown() が summary_content 内の見出しレベルを正規化する
        （### -> ####）。LLM は ## 内容 セクション内で ### サブ見出しを使用する。"""
        markdown_response = (
            "# Git ブランチ戦略\n"
            "\n"
            "## 要約\n"
            "Git のブランチ運用について。\n"
            "\n"
            "## 内容\n"
            "ブランチ戦略の解説。\n"
            "\n"
            "### メインブランチ\n"
            "main ブランチは本番環境に対応。\n"
            "\n"
            "### フィーチャーブランチ\n"
            "機能開発は feature/ プレフィックスで作成。\n"
            "\n"
            "#### 命名規則\n"
            "feature/issue-番号-概要 の形式。\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="Git戦略")
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # frontmatter 以降の本文を取得
        parts = output.split("---\n", 2)
        body = parts[2].strip()

        # summary_content 内の見出しが1レベル下がっている
        # 元の ### メインブランチ -> #### メインブランチ
        self.assertIn("#### メインブランチ", body)

        # 元の ### フィーチャーブランチ -> #### フィーチャーブランチ
        self.assertIn("#### フィーチャーブランチ", body)

        # 元の #### 命名規則 -> ##### 命名規則
        self.assertIn("##### 命名規則", body)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_no_h1_duplication(self, mock_call_ollama):
        """to_markdown() 出力に H1 見出し（# タイトル）が重複しない。
        frontmatter に title があるので、本文には H1 が存在しないことを確認。"""
        markdown_response = (
            "# Docker入門\n"
            "\n"
            "## 要約\n"
            "Dockerの基本概念と使い方。\n"
            "\n"
            "## 内容\n"
            "コンテナ技術の基礎を解説します。\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="Docker入門")
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # frontmatter 以降の本文
        parts = output.split("---\n", 2)
        body = parts[2].strip()

        # 本文に H1 が含まれない（summary_content は ## 内容 セクションの中身のみ）
        body_lines = body.split("\n")
        h1_lines = [
            line for line in body_lines if line.startswith("# ") and not line.startswith("##")
        ]
        self.assertEqual(
            len(h1_lines),
            0,
            f"本文に H1 が存在する: {h1_lines}",
        )

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_complete_format(self, mock_call_ollama):
        """to_markdown() の出力が従来の完全なフォーマットに一致する（統合検証）"""
        markdown_response = (
            "# APIエラーハンドリング\n"
            "\n"
            "## 要約\n"
            "REST APIにおけるエラーハンドリングのベストプラクティス。\n"
            "\n"
            "## 内容\n"
            "エラーレスポンスは適切なHTTPステータスコードを返すべきです。\n"
            "\n"
            "### ステータスコード\n"
            "- 400: Bad Request\n"
            "- 404: Not Found\n"
            "- 500: Internal Server Error\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(
            title="APIエラーハンドリング",
            created_at="2026-01-15T09:30:00",
        )
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # 完全な出力フォーマットを検証
        expected_frontmatter = (
            "---\n"
            "title: APIエラーハンドリング\n"
            "summary: REST APIにおけるエラーハンドリングのベストプラクティス。\n"
            "created: 2026-01-15\n"
            "source_provider: claude\n"
            "source_conversation: conv-001\n"
            "normalized: false\n"
            "---"
        )
        self.assertTrue(
            output.startswith(expected_frontmatter),
            f"Frontmatter mismatch.\nExpected:\n{expected_frontmatter}\n\nActual start:\n{output[:300]}",
        )

        # 本文にステータスコードリストが含まれる
        self.assertIn("- 400: Bad Request", output)
        self.assertIn("- 404: Not Found", output)

        # ### ステータスコード が #### に正規化されている
        self.assertIn("#### ステータスコード", output)
        # 正規化前の ### レベルが残っていないことを確認（行単位で検証）
        output_lines = output.split("\n")
        h3_status_lines = [l for l in output_lines if l.strip() == "### ステータスコード"]
        self.assertEqual(len(h3_status_lines), 0, "### ステータスコード が正規化されていない")

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_with_code_block_in_content(self, mock_call_ollama):
        """LLMレスポンスの ## 内容 にコードブロックが含まれる場合も正しく出力される"""
        markdown_response = (
            "# Python例外処理\n"
            "\n"
            "## 要約\n"
            "try-except パターンの解説。\n"
            "\n"
            "## 内容\n"
            "例外処理の基本パターン:\n"
            "\n"
            "```python\n"
            "try:\n"
            "    result = 1 / 0\n"
            "except ZeroDivisionError as e:\n"
            "    print(f'Error: {e}')\n"
            "```\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="Python例外処理")
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # コードブロックが出力に含まれる
        self.assertIn("```python", output)
        self.assertIn("except ZeroDivisionError", output)
        # frontmatter が正常
        self.assertIn("title: Python例外処理", output)
        self.assertIn("summary: try-except パターンの解説。", output)

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_with_english_summary_translation(self, mock_call_ollama):
        """英語サマリーの翻訳フローを経由しても to_markdown() の出力が正しい"""
        # call_ollama は2回呼ばれる: 1回目=翻訳、2回目=知識抽出
        translation_response = "## 要約\nPythonのデータクラスに関する議論。\n"
        extraction_response = (
            "# Pythonデータクラス\n"
            "\n"
            "## 要約\n"
            "dataclassデコレータの使い方。\n"
            "\n"
            "## 内容\n"
            "Python 3.7 から導入されたデータクラスの活用法。\n"
        )
        mock_call_ollama.side_effect = [
            (translation_response, None),  # translate_summary
            (extraction_response, None),  # extract (knowledge extraction)
        ]

        conversation = make_conversation(
            title="Pythonデータクラス",
            summary="**Conversation Overview** Discussion about Python dataclasses and their usage.",
            created_at="2026-01-20T14:00:00",
        )
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        # 翻訳されたサマリーが frontmatter に使用される
        self.assertIn("summary: Pythonのデータクラスに関する議論。", output)
        # LLM 出力のサマリーではなく翻訳結果が使われる
        self.assertNotIn("dataclassデコレータの使い方", output.split("---")[1])

    @patch("src.etl.utils.knowledge_extractor.call_ollama")
    def test_to_markdown_with_unicode_content(self, mock_call_ollama):
        """Unicode/日本語を含むマークダウンレスポンスが正しく処理される"""
        markdown_response = (
            "# 日本語プログラミング用語集\n"
            "\n"
            "## 要約\n"
            "主要なプログラミング用語の日本語訳まとめ。\n"
            "\n"
            "## 内容\n"
            "### 基本用語\n"
            "- 変数（へんすう）: variable\n"
            "- 関数（かんすう）: function\n"
            "- 配列（はいれつ）: array\n"
        )
        mock_call_ollama.return_value = (markdown_response, None)

        conversation = make_conversation(title="プログラミング用語集")
        result = self.extractor.extract(conversation)
        self.assertTrue(result.success)

        output = result.document.to_markdown()

        self.assertIn("title: プログラミング用語集", output)
        self.assertIn("変数（へんすう）: variable", output)
        self.assertIn("関数（かんすう）: function", output)
        # ### 基本用語 -> #### 基本用語 に正規化
        self.assertIn("#### 基本用語", output)


if __name__ == "__main__":
    unittest.main()
