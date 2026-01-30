"""
test_pipeline.py - パイプラインモジュールのテスト

normalizer.pipeline モジュールのテスト（Ollama API はモック）
"""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from normalizer.tests import read_fixture


class TestExtractDateFromFilename(unittest.TestCase):
    """extract_date_from_filename 関数のテスト"""

    def test_jekyll_format_hyphen(self):
        """Jekyll形式（ハイフン区切り）"""
        from normalizer.pipeline.stages import extract_date_from_filename

        date = extract_date_from_filename("2022-10-17-My-Post.md")
        self.assertEqual(date, "2022-10-17")

    def test_jekyll_format_underscore(self):
        """Jekyll形式（アンダースコア区切り）"""
        from normalizer.pipeline.stages import extract_date_from_filename

        date = extract_date_from_filename("2022_10_17_My_Post.md")
        self.assertEqual(date, "2022-10-17")

    def test_no_date(self):
        """日付なしファイル名"""
        from normalizer.pipeline.stages import extract_date_from_filename

        date = extract_date_from_filename("my-post.md")
        self.assertEqual(date, "")

    def test_partial_date(self):
        """不完全な日付"""
        from normalizer.pipeline.stages import extract_date_from_filename

        date = extract_date_from_filename("2022-10-Post.md")
        self.assertEqual(date, "")


class TestPreProcess(unittest.TestCase):
    """pre_process 関数のテスト"""

    def test_empty_content(self):
        """空コンテンツ"""
        from normalizer.pipeline.stages import pre_process

        result = pre_process(Path("/tmp/test.md"), "")

        self.assertTrue(result["is_empty"])
        self.assertIsNotNone(result["skip_reason"])

    def test_short_content(self):
        """極短文（50文字未満）"""
        from normalizer.pipeline.stages import pre_process

        result = pre_process(Path("/tmp/test.md"), "Short text")

        self.assertTrue(result["is_too_short"])
        self.assertIsNotNone(result["skip_reason"])

    def test_english_document(self):
        """英語文書の検出"""
        from normalizer.pipeline.stages import pre_process

        # 長い英語テキストを生成
        content = """# English Document

This is a comprehensive English document with multiple sections.
It contains detailed information about software development practices.

## Section One

Here we discuss various programming concepts and methodologies.
The content is purely in English to test the detection algorithm.

## Section Two

Additional content to ensure the document length exceeds the threshold.
This should be detected as a complete English document.

## Section Three

Final section with more technical content about development workflows.
"""
        result = pre_process(Path("/tmp/english.md"), content)

        self.assertTrue(result["is_english_doc"])

    def test_template_content(self):
        """テンプレート残骸の検出"""
        from normalizer.pipeline.stages import pre_process

        # 50文字以上にする
        content = """# Template Document with TODO

This is a document that contains a [TODO] item that needs completion.
Some placeholder text here to make it longer than minimum.
More content to ensure we pass the length check for proper testing.
"""
        result = pre_process(Path("/tmp/template.md"), content)

        self.assertTrue(result["has_template_markers"])
        self.assertIsNotNone(result["skip_reason"])

    def test_normal_content(self):
        """通常のコンテンツ（スキップしない）"""
        from normalizer.pipeline.stages import pre_process

        content = """# 日本語ドキュメント

これは通常の日本語ドキュメントです。
十分な長さがあり、テンプレートでもありません。
正規化処理を続行すべきです。
"""
        result = pre_process(Path("/tmp/normal.md"), content)

        self.assertFalse(result["is_empty"])
        self.assertFalse(result["is_too_short"])
        self.assertFalse(result["has_template_markers"])


# =============================================================================
# New Pipeline Stage Tests (Pipeline統合用)
# =============================================================================


class TestStageA(unittest.TestCase):
    """stage_a 関数のテスト（Ollamaモック）- Dust判定+ジャンル分類統合"""

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_a_dust(self, mock_load_prompt, mock_call_llm):
        """T009: dust判定テスト"""
        from normalizer.pipeline.stages import stage_a

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            '{"genre": "dust", "subfolder": "", "confidence": "high", "reason": "テスト投稿"}',
            None
        )

        result = stage_a("テスト", "test.md", is_english=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["genre"], "dust")
        self.assertEqual(result["data"]["confidence"], "high")
        self.assertEqual(result["data"]["reason"], "テスト投稿")
        self.assertEqual(result["data"]["subfolder"], "")

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_a_genre(self, mock_load_prompt, mock_call_llm):
        """T010: ジャンル分類テスト"""
        from normalizer.pipeline.stages import stage_a

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            '{"genre": "エンジニア", "subfolder": "Python", "confidence": "high", "reason": "Python開発に関する技術文書"}',
            None
        )

        result = stage_a("Pythonプログラミング入門", "python_intro.md", is_english=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["genre"], "エンジニア")
        self.assertEqual(result["data"]["subfolder"], "Python")
        self.assertEqual(result["data"]["confidence"], "high")

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_a_invalid_genre_fallback(self, mock_load_prompt, mock_call_llm):
        """無効なジャンルは「その他」にフォールバック"""
        from normalizer.pipeline.stages import stage_a

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            '{"genre": "無効なジャンル", "subfolder": "", "confidence": "high", "reason": "テスト"}',
            None
        )

        result = stage_a("コンテンツ", "test.md", is_english=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["genre"], "その他")


class TestStageC(unittest.TestCase):
    """stage_c 関数のテスト（Ollamaモック）- メタデータ生成"""

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_c_metadata(self, mock_load_prompt, mock_call_llm):
        """T016: メタデータ生成テスト"""
        from normalizer.pipeline.stages import stage_c

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            '{"title": "Pythonプログラミング入門", "tags": ["Python", "プログラミング", "入門"], "summary": "Pythonの基本文法と実践的な使い方を解説。", "related": [["Python環境構築"], ["pip使い方"]]}',
            None
        )

        result = stage_c("正規化されたコンテンツ", "python.md", "エンジニア")

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["title"], "Pythonプログラミング入門")
        self.assertEqual(len(result["data"]["tags"]), 3)
        self.assertIn("Python", result["data"]["tags"])
        self.assertEqual(result["data"]["summary"], "Pythonの基本文法と実践的な使い方を解説。")
        self.assertEqual(len(result["data"]["related"]), 2)

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_c_summary_max_length(self, mock_load_prompt, mock_call_llm):
        """T017: サマリー最大長テスト（200文字超過時に切り詰め）"""
        from normalizer.pipeline.stages import stage_c

        # 200文字を超えるサマリー
        long_summary = "あ" * 250

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            f'{{"title": "サマリー長さテスト用タイトル", "tags": ["tag"], "summary": "{long_summary}", "related": []}}',
            None
        )

        result = stage_c("コンテンツ", "test.md", "エンジニア")

        self.assertTrue(result["success"])
        self.assertLessEqual(len(result["data"]["summary"]), 200)

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_c_related_format(self, mock_load_prompt, mock_call_llm):
        """T018: 関連ノート形式テスト（内部リンク形式に正規化）"""
        from normalizer.pipeline.stages import stage_c

        mock_load_prompt.return_value = "system prompt"
        # 様々な形式の related を返す
        mock_call_llm.return_value = (
            '{"title": "関連ノート形式テスト用タイトル", "tags": ["tag"], "summary": "関連ノート形式のテストサマリー", "related": [["ノート1"], "ノート2", "[[ノート3]]"]}',
            None
        )

        result = stage_c("コンテンツ", "test.md", "エンジニア")

        self.assertTrue(result["success"])
        # 全て [[xxx]] 形式に正規化されていることを確認
        for item in result["data"]["related"]:
            self.assertTrue(item.startswith("[[") and item.endswith("]]"))

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_stage_c_empty_related(self, mock_load_prompt, mock_call_llm):
        """関連ノートが空配列でも正常に処理"""
        from normalizer.pipeline.stages import stage_c

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = (
            '{"title": "空関連ノートテスト用タイトル", "tags": ["tag"], "summary": "空の関連ノートテストサマリー", "related": []}',
            None
        )

        result = stage_c("コンテンツ", "test.md", "エンジニア")

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["related"], [])


class TestStage3Normalize(unittest.TestCase):
    """stage3_normalize 関数のテスト（Ollamaモック）"""

    @patch('normalizer.pipeline.stages.call_llm_for_stage')
    @patch('normalizer.pipeline.stages.load_prompt')
    def test_content_normalization(self, mock_load_prompt, mock_call_llm):
        """コンテンツ正規化"""
        from normalizer.pipeline.stages import stage3_normalize

        mock_load_prompt.return_value = "system prompt"
        mock_call_llm.return_value = ('{"normalized_content": "## セクション1\\n\\n整形されたコンテンツ", "improvements_made": ["見出し整形"]}', None)

        result = stage3_normalize("元のコンテンツ", "test.md", "エンジニア", is_english=False)

        self.assertTrue(result["success"])
        self.assertIn("## セクション1", result["data"]["normalized_content"])


class TestPostProcessV2(unittest.TestCase):
    """post_process_v2 関数のテスト"""

    def test_post_process_v2_normal(self):
        """新パイプラインの後処理（正常系）"""
        from normalizer.pipeline.stages import post_process_v2
        from normalizer.models import (
            PreProcessingResult,
            StageResult,
            StageAResult,
            Stage3Result,
            StageCResult,
        )

        pre_result: PreProcessingResult = {
            "is_empty": False,
            "is_too_short": False,
            "is_english_doc": False,
            "english_score": 0.0,
            "extracted_date": "2024-01-15",
            "has_template_markers": False,
            "skip_reason": None,
        }

        stage_a_result: StageResult = {
            "success": True,
            "data": StageAResult(genre="エンジニア", subfolder="Python", confidence="high", reason="Python技術文書"),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        stage_b_result: StageResult = {
            "success": True,
            "data": Stage3Result(normalized_content="## 正規化されたコンテンツ", improvements_made=["改善1"]),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        stage_c_result: StageResult = {
            "success": True,
            "data": StageCResult(title="Pythonガイド", tags=["Python", "プログラミング"], summary="Python入門", related=["[[Python基礎]]"], created="2024-01-15"),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        result = post_process_v2(
            pre_result,
            stage_a_result,
            stage_b_result,
            stage_c_result,
            Path("/tmp/test.md"),
        )

        self.assertEqual(result["genre"], "エンジニア")
        self.assertEqual(result["subfolder"], "Python")
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["reason"], "Python技術文書")
        self.assertEqual(result["frontmatter"]["title"], "Pythonガイド")
        self.assertEqual(result["frontmatter"]["summary"], "Python入門")
        self.assertEqual(result["frontmatter"]["related"], ["[[Python基礎]]"])

    def test_post_process_v2_low_confidence(self):
        """低確信度時も正常に処理される"""
        from normalizer.pipeline.stages import post_process_v2
        from normalizer.models import (
            PreProcessingResult,
            StageResult,
            StageAResult,
            Stage3Result,
            StageCResult,
        )

        pre_result: PreProcessingResult = {
            "is_empty": False,
            "is_too_short": False,
            "is_english_doc": False,
            "english_score": 0.0,
            "extracted_date": "2024-01-15",
            "has_template_markers": False,
            "skip_reason": None,
        }

        stage_a_result: StageResult = {
            "success": True,
            "data": StageAResult(genre="その他", subfolder="", confidence="low", reason="複数ジャンルにまたがる"),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        stage_b_result: StageResult = {
            "success": True,
            "data": Stage3Result(normalized_content="コンテンツ", improvements_made=[]),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        stage_c_result: StageResult = {
            "success": True,
            "data": StageCResult(title="タイトル", tags=[], summary="", related=[], created=""),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        result = post_process_v2(
            pre_result,
            stage_a_result,
            stage_b_result,
            stage_c_result,
            Path("/tmp/test.md"),
        )

        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["genre"], "その他")


class TestRunPipelineV2(unittest.TestCase):
    """run_pipeline_v2 関数のテスト"""

    @patch("normalizer.pipeline.runner.stage_a")
    @patch("normalizer.pipeline.runner.stage3_normalize")
    @patch("normalizer.pipeline.runner.stage_c")
    def test_full_flow(self, mock_stage_c, mock_stage_b, mock_stage_a):
        """T024: 完全フロー（A→B→C）"""
        from normalizer.pipeline.runner import run_pipeline_v2
        from normalizer.models import StageAResult, Stage3Result, StageCResult

        # Stage Aのモック
        mock_stage_a.return_value = {
            "success": True,
            "data": StageAResult(genre="エンジニア", subfolder="Python", confidence="high", reason="技術文書"),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        # Stage B (stage3_normalize)のモック
        mock_stage_b.return_value = {
            "success": True,
            "data": Stage3Result(normalized_content="## 正規化コンテンツ", improvements_made=["改善"]),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        # Stage Cのモック
        mock_stage_c.return_value = {
            "success": True,
            "data": StageCResult(title="Pythonガイド", tags=["Python"], summary="要約", related=[], created=""),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        content = "x" * 100  # 十分な長さのコンテンツ
        result = run_pipeline_v2(Path("/tmp/test.md"), content)

        # 全3ステージが呼ばれたことを確認
        mock_stage_a.assert_called_once()
        mock_stage_b.assert_called_once()
        mock_stage_c.assert_called_once()

        # 結果の確認
        self.assertEqual(result["genre"], "エンジニア")
        self.assertEqual(result["subfolder"], "Python")
        self.assertEqual(result["frontmatter"]["title"], "Pythonガイド")
        self.assertEqual(result["frontmatter"]["summary"], "要約")

    @patch("normalizer.pipeline.runner.stage_a")
    def test_dust_skip(self, mock_stage_a):
        """T025: Dust判定時のB/Cスキップ"""
        from normalizer.pipeline.runner import run_pipeline_v2
        from normalizer.models import StageAResult

        # Stage A: dust判定
        mock_stage_a.return_value = {
            "success": True,
            "data": StageAResult(genre="dust", subfolder="", confidence="high", reason="無意味なメモ"),
            "error": None,
            "retry_count": 0,
            "raw_response": None,
        }

        content = "x" * 100
        result = run_pipeline_v2(Path("/tmp/dust.md"), content)

        # Stage Aのみ呼ばれ、B/Cは呼ばれない
        mock_stage_a.assert_called_once()

        # 結果の確認
        self.assertEqual(result["genre"], "dust")
        self.assertEqual(result["reason"], "無意味なメモ")
        self.assertEqual(result["normalized_content"], "")

if __name__ == "__main__":
    unittest.main()
