"""Unit tests for parse_markdown_response() in src.etl.utils.ollama.

Tests for:
- T007: Standard markdown input -> dict conversion
- T008: Edge cases (code block fences, heading levels, plain text fallback, empty input)
- T009: Summary translation minimal markdown -> dict{"summary": ...}
"""

import unittest

from src.etl.utils.ollama import parse_markdown_response


class TestParseMarkdownResponseStandard(unittest.TestCase):
    """T007: 標準マークダウン入力 -> dict 変換テスト"""

    def test_standard_three_section_markdown(self):
        """標準的な3セクション構成のマークダウンが正しくパースされる"""
        response = (
            "# Pythonのデコレータパターン\n"
            "\n"
            "## 要約\n"
            "Pythonのデコレータを使った関数拡張パターンについての議論。\n"
            "\n"
            "## 内容\n"
            "デコレータは関数を引数として受け取り、新しい関数を返す高階関数です。\n"
            "\n"
            "### 基本構文\n"
            "```python\n"
            "def my_decorator(func):\n"
            "    def wrapper(*args):\n"
            "        return func(*args)\n"
            "    return wrapper\n"
            "```\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "Pythonのデコレータパターン")
        self.assertIn("デコレータを使った関数拡張パターン", data["summary"])
        self.assertIn("高階関数", data["summary_content"])
        self.assertIn("```python", data["summary_content"])

    def test_title_extracted_from_h1(self):
        """# 見出しからタイトルが正しく抽出される"""
        response = "# テストタイトル\n\n## 要約\n要約文。\n\n## 内容\n内容テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "テストタイトル")

    def test_summary_extracted_from_section(self):
        """## 要約 セクションの本文が summary に入る"""
        response = (
            "# タイトル\n\n## 要約\nこれは要約です。重要なポイントを含みます。\n\n## 内容\n本文。\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["summary"], "これは要約です。重要なポイントを含みます。")

    def test_content_extracted_from_section(self):
        """## 内容 セクションの本文が summary_content に入る"""
        response = "# タイトル\n\n## 要約\n要約文。\n\n## 内容\n詳細な内容がここに入ります。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["summary_content"], "詳細な内容がここに入ります。")

    def test_multiline_content_preserved(self):
        """複数行の内容がそのまま保持される"""
        content_text = "行1\n\n行2\n\n- リスト1\n- リスト2"
        response = f"# タイトル\n\n## 要約\n要約。\n\n## 内容\n{content_text}\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertIn("行1", data["summary_content"])
        self.assertIn("リスト1", data["summary_content"])

    def test_return_type_is_tuple(self):
        """戻り値が tuple[dict, str | None] であること"""
        response = "# タイトル\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        result = parse_markdown_response(response)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)

    def test_all_three_keys_present(self):
        """出力 dict に title, summary, summary_content の3キーが存在する"""
        response = "# タイトル\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertIn("title", data)
        self.assertIn("summary", data)
        self.assertIn("summary_content", data)

    def test_unicode_content_preserved(self):
        """日本語・英語混在コンテンツが正しく保持される"""
        response = (
            "# Docker Composeの設定方法\n"
            "\n"
            "## 要約\n"
            "Docker Compose を使ったマルチコンテナ環境の構築について説明。\n"
            "\n"
            "## 内容\n"
            "docker-compose.yml で services を定義します。\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "Docker Composeの設定方法")
        self.assertIn("Docker Compose", data["summary"])


class TestParseMarkdownResponseEdgeCases(unittest.TestCase):
    """T008: エッジケーステスト"""

    def test_code_block_fence_removal(self):
        """```markdown ... ``` で囲まれたレスポンスからフェンスが除去される"""
        response = (
            "```markdown\n# タイトル\n\n## 要約\n要約テキスト。\n\n## 内容\n内容テキスト。\n```\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "タイトル")
        self.assertEqual(data["summary"], "要約テキスト。")

    def test_code_block_fence_without_language(self):
        """言語指定なしの ``` フェンスも除去される"""
        response = "```\n# タイトル\n\n## 要約\n要約。\n\n## 内容\n内容。\n```\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "タイトル")

    def test_h2_as_title_when_no_h1(self):
        """H1 がない場合、最初の ## 見出しをタイトルとして扱う"""
        response = "## タイトル代わりの見出し\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "タイトル代わりの見出し")

    def test_h3_as_title_when_no_h1_h2(self):
        """H1/H2 がない場合、### 見出しをタイトルとして扱う"""
        response = "### タイトル\n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "タイトル")

    def test_plain_text_fallback(self):
        """見出しがないプレーンテキストの場合、全体を要約として扱う"""
        response = (
            "これは見出しのないプレーンテキストのレスポンスです。LLMが構造を無視して回答した場合。"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        # プレーンテキストの場合: 先頭行からタイトル生成、全体を summary として扱う
        self.assertIn("summary", data)
        self.assertTrue(len(data["summary"]) > 0)

    def test_empty_input_returns_error(self):
        """空入力の場合はエラーを返す"""
        data, error = parse_markdown_response("")
        self.assertIsNotNone(error)
        self.assertEqual(data, {})

    def test_whitespace_only_input_returns_error(self):
        """空白のみの入力はエラーを返す"""
        data, error = parse_markdown_response("   \n\n  \t  ")
        self.assertIsNotNone(error)
        self.assertEqual(data, {})

    def test_none_input_returns_error(self):
        """None 入力はエラーを返す"""
        data, error = parse_markdown_response(None)
        self.assertIsNotNone(error)
        self.assertEqual(data, {})

    def test_missing_summary_section_uses_default(self):
        """## 要約 セクションがない場合、空文字がデフォルト"""
        response = "# タイトル\n\n## 内容\n内容テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["summary"], "")

    def test_missing_content_section_uses_default(self):
        """## 内容 セクションがない場合、空文字がデフォルト"""
        response = "# タイトル\n\n## 要約\n要約テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["summary_content"], "")

    def test_missing_title_uses_default(self):
        """タイトル見出しがない場合、空文字がデフォルト（要約・内容セクションあり）"""
        response = "## 要約\n要約テキスト。\n\n## 内容\n内容テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "")

    def test_extra_whitespace_in_heading_stripped(self):
        """見出しの前後の空白が除去される"""
        response = "#   余白ありタイトル  \n\n## 要約\n要約。\n\n## 内容\n内容。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data["title"], "余白ありタイトル")

    def test_content_with_code_blocks_preserved(self):
        """内容セクション内のコードブロックが保持される"""
        response = (
            "# タイトル\n"
            "\n"
            "## 要約\n"
            "要約。\n"
            "\n"
            "## 内容\n"
            "以下はサンプルコードです:\n"
            "\n"
            "```python\n"
            "print('hello')\n"
            "```\n"
            "\n"
            "上記のコードを実行します。\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertIn("```python", data["summary_content"])
        self.assertIn("print('hello')", data["summary_content"])


class TestParseMarkdownResponseSummaryTranslation(unittest.TestCase):
    """T009: summary_translation.txt 用の最小マークダウンパーステスト"""

    def test_summary_only_markdown(self):
        """## 要約 セクションのみのマークダウンが正しくパースされる"""
        response = "## 要約\nPythonデコレータパターンについての技術的な議論の要約です。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertIn("summary", data)
        self.assertEqual(
            data["summary"],
            "Pythonデコレータパターンについての技術的な議論の要約です。",
        )

    def test_summary_only_with_multiline(self):
        """複数行の要約テキストが正しく抽出される"""
        response = (
            "## 要約\nDockerを使ったコンテナ化について。\nマルチステージビルドの利点も含む。\n"
        )
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertIn("Docker", data["summary"])
        self.assertIn("マルチステージビルド", data["summary"])

    def test_summary_only_title_defaults_empty(self):
        """要約のみの場合、title は空文字"""
        response = "## 要約\n翻訳された要約テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data.get("title", ""), "")

    def test_summary_only_content_defaults_empty(self):
        """要約のみの場合、summary_content は空文字"""
        response = "## 要約\n翻訳された要約テキスト。\n"
        data, error = parse_markdown_response(response)
        self.assertIsNone(error)
        self.assertEqual(data.get("summary_content", ""), "")


if __name__ == "__main__":
    unittest.main()
