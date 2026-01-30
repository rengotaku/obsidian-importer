"""
llm_import.tests.test_knowledge_extractor - KnowledgeExtractor のテスト

LLM 呼び出しはモックを使用してテスト。
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象モジュール（後で実装）
# from scripts.llm_import.common.knowledge_extractor import (
#     KnowledgeExtractor,
#     KnowledgeDocument,
#     CodeSnippet,
# )


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# Mock LLM Response
# =============================================================================

# 新仕様: title, tags, related_keywords, action_items を削除
# summary, summary_content を追加
MOCK_LLM_RESPONSE = """{
  "summary": "卓上IHヒーターを使ってピザを安全に保温する方法についての質問と回答",
  "summary_content": "### IHでピザを保温するポイント\\n\\n- IH対応の金属プレートや鉄板の上にピザを置く\\n- ピザの箱を直接IHに置くと発火の危険がある\\n- 最弱火力で保温する\\n\\n| 方法 | 注意点 |\\n|------|--------|\\n| スキレット使用 | 蓋で覆うと均一に温まる |\\n| 鉄板使用 | アルミホイルで覆う |",
  "key_learnings": [
    "IH対応の金属プレートや鉄板の上にピザを置くことで保温可能",
    "ピザの箱を直接IHに置くと発火の危険がある",
    "温度が高すぎると底だけ焦げてチーズは冷たいままになる",
    "蓋やアルミホイルを軽くかぶせると熱が上にも回る"
  ],
  "code_snippets": []
}"""

MOCK_LLM_RESPONSE_WITH_CODE = """{
  "summary": "Git SSH認証で permission denied エラーが発生した問題の解決方法",
  "summary_content": "### 解決手順\\n\\n1. ssh-agent を起動する\\n2. ssh-add で秘密鍵を登録する\\n3. ~/.ssh/config で IdentityFile を指定",
  "key_learnings": [
    "ssh-agent が動作していないと認証エラーになる",
    "ssh-add コマンドで鍵を登録する必要がある",
    "~/.ssh/config で IdentityFile を指定すると便利"
  ],
  "code_snippets": [
    {
      "language": "bash",
      "code": "eval $(ssh-agent -s)\\nssh-add ~/.ssh/id_rsa",
      "description": "ssh-agent の起動と鍵の登録"
    }
  ]
}"""

# Summary 翻訳用のモックレスポンス
MOCK_TRANSLATION_RESPONSE = """{
  "summary": "ユーザーがGit SSH認証エラーの解決方法について質問した"
}"""


# =============================================================================
# Test Cases
# =============================================================================


class TestKnowledgeExtractor(unittest.TestCase):
    """KnowledgeExtractor のテスト"""

    def setUp(self):
        """テストセットアップ"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
        self.extractor = KnowledgeExtractor()

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_basic_without_summary(self, mock_ollama):
        """Summary なしの基本的な抽出（1段階 LLM）"""
        mock_ollama.return_value = (MOCK_LLM_RESPONSE, None)

        # テスト用の会話データを作成
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="ピザを卓上ihにおいて保温するのあり？",
                timestamp="2025-12-20T09:28:27.095076Z",
                sender="human",
            ),
            ClaudeMessage(
                uuid="msg-2",
                content="ありですね！IH対応のプレートを使えば保温できます。",
                timestamp="2025-12-20T09:28:35.295436Z",
                sender="assistant",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="卓上IHでピザを保温する方法",
            created_at="2025-12-20T09:28:24.439525Z",
            updated_at="2025-12-20T09:28:36.680746Z",
            summary=None,  # Summary なし
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        # タイトルは会話タイトルから取得（日付プレフィックス除去）
        self.assertEqual(result.document.title, "卓上IHでピザを保温する方法")
        # summary は LLM 出力から
        self.assertIn("IH", result.document.summary)
        # summary_content は構造化された形式
        self.assertIn("###", result.document.summary_content)
        # LLM は1回だけ呼ばれる
        self.assertEqual(mock_ollama.call_count, 1)

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_with_english_summary(self, mock_ollama):
        """英語 Summary ありの抽出（2段階 LLM）"""
        # 1回目: 翻訳、2回目: まとめ生成
        mock_ollama.side_effect = [
            (MOCK_TRANSLATION_RESPONSE, None),  # Step 1: 翻訳
            (MOCK_LLM_RESPONSE_WITH_CODE, None),  # Step 2: まとめ生成
        ]

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Git SSH認証エラーが出ます",
                timestamp="2025-12-20T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="2025-12-20_Git SSH認証エラー",  # 日付プレフィックスあり
            created_at="2025-12-20T10:00:00Z",
            updated_at="2025-12-20T10:00:00Z",
            summary="**Conversation Overview**\n\nThe user asked about Git SSH authentication errors.",
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertTrue(result.success)
        # タイトルから日付プレフィックスが除去される
        self.assertEqual(result.document.title, "Git SSH認証エラー")
        # summary は翻訳結果を使用
        self.assertIn("Git SSH認証エラー", result.document.summary)
        # LLM は2回呼ばれる（翻訳 + まとめ生成）
        self.assertEqual(mock_ollama.call_count, 2)

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_with_code_snippets(self, mock_ollama):
        """コードスニペット付き抽出"""
        mock_ollama.return_value = (MOCK_LLM_RESPONSE_WITH_CODE, None)

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Git SSH認証エラーが出ます",
                timestamp="2025-12-20T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Git SSH認証エラー",
            created_at="2025-12-20T10:00:00Z",
            updated_at="2025-12-20T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertTrue(result.success)
        self.assertEqual(len(result.document.code_snippets), 1)
        self.assertEqual(result.document.code_snippets[0].language, "bash")

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_api_error(self, mock_ollama):
        """API エラー時の処理"""
        mock_ollama.return_value = ("", "接続エラー: Connection refused")

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Test",
                timestamp="2026-01-16T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Test",
            created_at="2026-01-16T10:00:00Z",
            updated_at="2026-01-16T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertFalse(result.success)
        self.assertIn("接続エラー", result.error)

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_invalid_json(self, mock_ollama):
        """不正な JSON レスポンス時の処理"""
        mock_ollama.return_value = ("This is not JSON", None)

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Test",
                timestamp="2026-01-16T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Test",
            created_at="2026-01-16T10:00:00Z",
            updated_at="2026-01-16T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertFalse(result.success)
        self.assertIn("JSON", result.error)

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_translation_error(self, mock_ollama):
        """翻訳エラー時の処理"""
        mock_ollama.return_value = ("", "翻訳 API エラー")

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Test",
                timestamp="2026-01-16T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Test",
            created_at="2026-01-16T10:00:00Z",
            updated_at="2026-01-16T10:00:00Z",
            summary="**Conversation Overview**\n\nThe user asked about testing.",
            _messages=messages,
        )

        result = self.extractor.extract(conv)

        self.assertFalse(result.success)
        self.assertIn("Summary 翻訳エラー", result.error)


class TestKnowledgeDocument(unittest.TestCase):
    """KnowledgeDocument のテスト"""

    def test_to_markdown(self):
        """Markdown 出力が正しい形式であること"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument, CodeSnippet

        doc = KnowledgeDocument(
            title="テストタイトル",
            summary="これはテスト要約です。",
            created="2026-01-16",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="### テストセクション\n\n- ポイント1\n- ポイント2",
            key_learnings=["学び1", "学び2"],
            code_snippets=[],
        )

        md = doc.to_markdown()

        # frontmatter
        self.assertIn("---", md)
        self.assertIn("title: テストタイトル", md)
        self.assertIn("summary: これはテスト要約です。", md)
        self.assertIn("normalized: false", md)
        self.assertIn("source_provider: claude", md)

        # 本文（新仕様: # から始まる）
        self.assertIn("# まとめ", md)
        self.assertIn("#### テストセクション", md)  # ### → #### (1レベル下げ)
        self.assertIn("# 主要な学び", md)
        self.assertIn("- 学び1", md)

        # 削除されたセクションがないこと
        self.assertNotIn("## 概要", md)
        self.assertNotIn("## 実践的なアクション", md)
        self.assertNotIn("## 関連", md)
        self.assertNotIn("tags:", md)

    def test_to_markdown_with_code(self):
        """コードスニペット付き Markdown 出力"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument, CodeSnippet

        doc = KnowledgeDocument(
            title="コードテスト",
            summary="コードサンプル",
            created="2026-01-16",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="コードの説明",
            key_learnings=["学び1"],
            code_snippets=[
                CodeSnippet(language="python", code="print('hello')", description="挨拶出力")
            ],
        )

        md = doc.to_markdown()

        self.assertIn("# コードスニペット", md)
        self.assertIn("## 挨拶出力", md)  # ### → ## (新仕様)
        self.assertIn("```python", md)
        self.assertIn("print('hello')", md)


class TestCodeSnippet(unittest.TestCase):
    """CodeSnippet のテスト"""

    def test_code_snippet_creation(self):
        """CodeSnippet が正しく作成されること"""
        from scripts.llm_import.common.knowledge_extractor import CodeSnippet

        snippet = CodeSnippet(
            language="python",
            code="print('test')",
            description="テスト出力",
        )
        self.assertEqual(snippet.language, "python")
        self.assertEqual(snippet.code, "print('test')")
        self.assertEqual(snippet.description, "テスト出力")


class TestEnglishSummaryDetection(unittest.TestCase):
    """英語サマリー検出のテスト"""

    def setUp(self):
        """テストセットアップ"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
        self.extractor = KnowledgeExtractor()

    def test_detect_conversation_overview_format(self):
        """Conversation Overview 形式の検出"""
        summary = "**Conversation Overview**\n\nThe user asked about..."
        self.assertTrue(self.extractor.is_english_summary(summary))

    def test_detect_plain_conversation_overview(self):
        """プレーン Conversation Overview の検出"""
        summary = "Conversation Overview\n\nThe user wanted to know..."
        self.assertTrue(self.extractor.is_english_summary(summary))

    def test_detect_the_user_pattern(self):
        """'The user' パターンの検出"""
        summary = "The user asked about how to configure..."
        self.assertTrue(self.extractor.is_english_summary(summary))

    def test_detect_high_ascii_ratio(self):
        """ASCII 比率による英語判定"""
        summary = "This is a long English summary about technical topics."
        self.assertTrue(self.extractor.is_english_summary(summary))

    def test_japanese_summary_not_detected(self):
        """日本語サマリーは英語として検出されない"""
        summary = "ユーザーがピザの保温方法について質問しました。"
        self.assertFalse(self.extractor.is_english_summary(summary))

    def test_mixed_content_japanese_dominant(self):
        """日本語が主の混合コンテンツ"""
        # 日本語が十分に含まれる文字列（ASCII比率が70%未満）
        summary = "これはテストです。日本語がメインの文章で、一部に English words が含まれています。"
        # 日本語文字が多いので False
        self.assertFalse(self.extractor.is_english_summary(summary))

    def test_empty_summary(self):
        """空サマリー"""
        self.assertFalse(self.extractor.is_english_summary(""))
        self.assertFalse(self.extractor.is_english_summary(None))


class TestUserMessageBuilding(unittest.TestCase):
    """ユーザーメッセージ構築のテスト"""

    def setUp(self):
        """テストセットアップ"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
        self.extractor = KnowledgeExtractor()

    def test_build_user_message_with_summary(self):
        """Summary 含むメッセージ構築（exclude_summary=False）"""
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Test message",
                timestamp="2026-01-16T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Test Conversation",
            created_at="2026-01-16T10:00:00Z",
            updated_at="2026-01-16T10:00:00Z",
            summary="日本語のサマリーです。",
            _messages=messages,
        )

        user_message = self.extractor._build_user_message(conv, exclude_summary=False)

        self.assertIn("会話サマリー: 日本語のサマリーです。", user_message)

    def test_build_user_message_without_summary(self):
        """Summary 除外メッセージ構築（exclude_summary=True）"""
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="Test message",
                timestamp="2026-01-16T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Test Conversation",
            created_at="2026-01-16T10:00:00Z",
            updated_at="2026-01-16T10:00:00Z",
            summary="This is an English summary.",
            _messages=messages,
        )

        user_message = self.extractor._build_user_message(conv, exclude_summary=True)

        # Summary は含まれない
        self.assertIn("会話サマリー: なし", user_message)
        self.assertNotIn("English summary", user_message)


class TestTitleCleaning(unittest.TestCase):
    """タイトルクリーニングのテスト"""

    def setUp(self):
        """テストセットアップ"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
        self.extractor = KnowledgeExtractor()

    def test_clean_title_with_date_prefix(self):
        """日付プレフィックス付きタイトルのクリーニング"""
        self.assertEqual(
            self.extractor._clean_title("2025-12-20_Git SSH認証エラー"),
            "Git SSH認証エラー"
        )

    def test_clean_title_with_date_only(self):
        """日付のみのプレフィックス"""
        self.assertEqual(
            self.extractor._clean_title("2025-12-20Git SSH認証エラー"),
            "Git SSH認証エラー"
        )

    def test_clean_title_without_date(self):
        """日付プレフィックスなしのタイトル"""
        self.assertEqual(
            self.extractor._clean_title("Git SSH認証エラー"),
            "Git SSH認証エラー"
        )

    def test_clean_title_empty_after_date(self):
        """日付除去後が空の場合は元のタイトルを返す"""
        self.assertEqual(
            self.extractor._clean_title("2025-12-20_"),
            "2025-12-20_"
        )


class TestExtractorChunking(unittest.TestCase):
    """T016: KnowledgeExtractor チャンク分割のテスト"""

    def setUp(self):
        """テストセットアップ"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
        self.extractor = KnowledgeExtractor(chunk_size=25000, overlap_messages=2)

    def test_should_chunk_large_conversation(self):
        """大きい会話はチャンク対象と判定される"""
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        # 30,000文字のメッセージを作成
        large_content = "x" * 30000
        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content=large_content,
                timestamp="2026-01-17T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Large Conversation",
            created_at="2026-01-17T10:00:00Z",
            updated_at="2026-01-17T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        self.assertTrue(self.extractor.should_chunk(conv))

    def test_should_not_chunk_small_conversation(self):
        """小さい会話はチャンク対象外と判定される"""
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="短いメッセージです。",
                timestamp="2026-01-17T10:00:00Z",
                sender="human",
            ),
        ]
        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Small Conversation",
            created_at="2026-01-17T10:00:00Z",
            updated_at="2026-01-17T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        self.assertFalse(self.extractor.should_chunk(conv))

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_chunked_returns_list(self, mock_ollama):
        """extract_chunked() がリストを返す"""
        mock_ollama.return_value = (MOCK_LLM_RESPONSE, None)

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        # 各 15,000 文字 × 3 メッセージ = 45,000 文字
        messages = []
        for i in range(3):
            messages.append(
                ClaudeMessage(
                    uuid=f"msg-{i}",
                    content="x" * 15000,
                    timestamp="2026-01-17T10:00:00Z",
                    sender="human" if i % 2 == 0 else "assistant",
                )
            )

        conv = ClaudeConversation(
            uuid="test-uuid",
            title="Chunked Conversation",
            created_at="2026-01-17T10:00:00Z",
            updated_at="2026-01-17T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        results = self.extractor.extract_chunked(conv)

        # リストが返る
        self.assertIsInstance(results, list)
        # 複数チャンクに分割される
        self.assertGreater(len(results), 1)

        # 各結果は (ファイル名, ExtractionResult) タプル
        for filename, result in results:
            self.assertIsInstance(filename, str)
            self.assertTrue(filename.endswith(".md"))
            self.assertTrue("_00" in filename)  # 連番付き

    @patch('scripts.llm_import.common.knowledge_extractor.call_ollama')
    def test_extract_chunked_filename_format(self, mock_ollama):
        """チャンクファイル名のフォーマット"""
        mock_ollama.return_value = (MOCK_LLM_RESPONSE, None)

        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        messages = [
            ClaudeMessage(
                uuid="msg-1",
                content="x" * 30000,
                timestamp="2026-01-17T10:00:00Z",
                sender="human",
            ),
        ]

        conv = ClaudeConversation(
            uuid="test-uuid",
            title="2026-01-17_Long Title",
            created_at="2026-01-17T10:00:00Z",
            updated_at="2026-01-17T10:00:00Z",
            summary=None,
            _messages=messages,
        )

        results = self.extractor.extract_chunked(conv)

        # 日付プレフィックスが除去されている
        filename, _ = results[0]
        self.assertIn("Long Title", filename)
        self.assertIn("_001.md", filename)


class TestKnowledgeDocumentFileId(unittest.TestCase):
    """T007-T008: KnowledgeDocument の file_id フィールドのテスト"""

    def test_file_id_field_default_empty(self):
        """T007: file_id フィールドがデフォルトで空文字"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        doc = KnowledgeDocument(
            title="テスト",
            summary="要約",
            created="2026-01-18",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="内容",
            key_learnings=["学び"],
        )
        self.assertEqual(doc.file_id, "")

    def test_file_id_field_can_be_set(self):
        """T007: file_id フィールドに値を設定できる"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        doc = KnowledgeDocument(
            title="テスト",
            summary="要約",
            created="2026-01-18",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="内容",
            key_learnings=["学び"],
            file_id="a1b2c3d4e5f6",
        )
        self.assertEqual(doc.file_id, "a1b2c3d4e5f6")

    def test_to_markdown_includes_file_id_in_frontmatter(self):
        """T008: to_markdown() が frontmatter に file_id を出力する"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        doc = KnowledgeDocument(
            title="テスト",
            summary="要約",
            created="2026-01-18",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="内容",
            key_learnings=["学び"],
            file_id="a1b2c3d4e5f6",
        )

        md = doc.to_markdown()

        # file_id が frontmatter に含まれる
        self.assertIn("file_id: a1b2c3d4e5f6", md)

    def test_to_markdown_file_id_position_before_normalized(self):
        """T008: file_id は normalized の前に出力される"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        doc = KnowledgeDocument(
            title="テスト",
            summary="要約",
            created="2026-01-18",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="内容",
            key_learnings=["学び"],
            file_id="a1b2c3d4e5f6",
        )

        md = doc.to_markdown()

        # file_id と normalized の位置を確認
        file_id_pos = md.find("file_id:")
        normalized_pos = md.find("normalized:")
        self.assertGreater(file_id_pos, 0, "file_id が見つからない")
        self.assertGreater(normalized_pos, 0, "normalized が見つからない")
        self.assertLess(file_id_pos, normalized_pos, "file_id は normalized の前にあるべき")

    def test_to_markdown_empty_file_id_not_output(self):
        """T008: 空の file_id は frontmatter に出力されない"""
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        doc = KnowledgeDocument(
            title="テスト",
            summary="要約",
            created="2026-01-18",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="内容",
            key_learnings=["学び"],
            file_id="",  # 空文字
        )

        md = doc.to_markdown()

        # 空の file_id は出力されない
        self.assertNotIn("file_id:", md)


class TestExtractFileIdFromFrontmatter(unittest.TestCase):
    """T021/T023: extract_file_id_from_frontmatter のテスト"""

    def test_extracts_file_id_from_valid_frontmatter(self):
        """有効な frontmatter から file_id を抽出できる"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        content = """---
title: Test Title
file_id: a1b2c3d4e5f6
normalized: false
---

# Content here
"""
        result = extract_file_id_from_frontmatter(content)
        self.assertEqual(result, "a1b2c3d4e5f6")

    def test_extracts_file_id_at_different_position(self):
        """file_id が frontmatter 内の別の位置にあっても抽出できる"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        content = """---
title: Test Title
summary: Some summary
created: 2026-01-18
source_provider: claude
source_conversation: test-uuid
file_id: deadbeef1234
normalized: true
---

# まとめ
"""
        result = extract_file_id_from_frontmatter(content)
        self.assertEqual(result, "deadbeef1234")

    def test_returns_none_for_missing_file_id(self):
        """file_id がない場合は None を返す"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        content = """---
title: Test Title
normalized: false
---

# Content here
"""
        result = extract_file_id_from_frontmatter(content)
        self.assertIsNone(result)

    def test_returns_none_for_no_frontmatter(self):
        """frontmatter がない場合は None を返す"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        content = """# Just Content
No frontmatter here.
"""
        result = extract_file_id_from_frontmatter(content)
        self.assertIsNone(result)

    def test_returns_none_for_invalid_file_id_format(self):
        """file_id が無効な形式の場合は None を返す"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        # 12文字未満
        content1 = """---
title: Test
file_id: abc123
---
"""
        self.assertIsNone(extract_file_id_from_frontmatter(content1))

        # 大文字を含む（小文字のみ許可）
        content2 = """---
title: Test
file_id: A1B2C3D4E5F6
---
"""
        self.assertIsNone(extract_file_id_from_frontmatter(content2))

        # 非16進数文字を含む
        content3 = """---
title: Test
file_id: ghijklmnopqr
---
"""
        self.assertIsNone(extract_file_id_from_frontmatter(content3))

    def test_returns_none_for_empty_content(self):
        """空の content の場合は None を返す"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        self.assertIsNone(extract_file_id_from_frontmatter(""))

    def test_does_not_match_file_id_outside_frontmatter(self):
        """frontmatter 外の file_id にはマッチしない"""
        from scripts.llm_import.common.knowledge_extractor import extract_file_id_from_frontmatter

        content = """---
title: Test
---

# Content
file_id: a1b2c3d4e5f6
"""
        result = extract_file_id_from_frontmatter(content)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
