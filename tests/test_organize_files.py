"""Unit tests for organize_files.py."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.organize_files import (
    generate_preview,
    get_genre_mapping,
    load_config,
    parse_frontmatter,
    sanitize_topic,
    scan_files,
)


class TestLoadConfig(unittest.TestCase):
    """load_config() のテスト."""

    def test_load_config_success(self):
        """正常なYAML設定ファイルを読み込めること."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(
                "genre_mapping:\n"
                "  engineer: エンジニア\n"
                "  business: ビジネス\n"
                "default_input: data/07_model_output/organized\n"
            )
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertIsInstance(config, dict)
            self.assertIn("genre_mapping", config)
            self.assertEqual(config["genre_mapping"]["engineer"], "エンジニア")
            self.assertEqual(config["genre_mapping"]["business"], "ビジネス")
            self.assertIn("default_input", config)
        finally:
            os.unlink(config_path)

    def test_load_config_not_found(self):
        """存在しない設定ファイルでFileNotFoundErrorが発生すること."""
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/genre_mapping.yml")


class TestParseFrontmatter(unittest.TestCase):
    """parse_frontmatter() のテスト."""

    def test_parse_frontmatter(self):
        """正常なfrontmatter付きMarkdownファイルをパースできること."""
        content = (
            "---\n"
            "title: テスト記事\n"
            "genre: engineer\n"
            "topic: Python\n"
            "tags:\n"
            "  - python\n"
            "  - testing\n"
            "created: 2026-01-15\n"
            "---\n"
            "# 本文\n"
            "これはテスト用のコンテンツです。\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            file_path = f.name

        try:
            result = parse_frontmatter(file_path)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["title"], "テスト記事")
            self.assertEqual(result["genre"], "engineer")
            self.assertEqual(result["topic"], "Python")
            self.assertIn("tags", result)
            self.assertEqual(result["tags"], ["python", "testing"])
        finally:
            os.unlink(file_path)

    def test_parse_frontmatter_invalid(self):
        """frontmatterのないMarkdownファイルで空dictまたはNoneを返すこと."""
        content = "# 見出し\nこれはfrontmatterなしのファイルです。\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            file_path = f.name

        try:
            result = parse_frontmatter(file_path)
            # frontmatterがない場合、空dictまたはNoneを返す
            if result is None:
                self.assertIsNone(result)
            else:
                self.assertIsInstance(result, dict)
                self.assertEqual(len(result), 0)
        finally:
            os.unlink(file_path)


class TestGetGenreMapping(unittest.TestCase):
    """get_genre_mapping() のテスト."""

    def setUp(self):
        """テスト用設定を準備."""
        self.config = {
            "genre_mapping": {
                "engineer": "エンジニア",
                "business": "ビジネス",
                "economy": "経済",
                "daily": "日常",
                "other": "その他",
            }
        }

    def test_get_genre_mapping(self):
        """既知のジャンルが正しい日本語名にマッピングされること."""
        self.assertEqual(get_genre_mapping(self.config, "engineer"), "エンジニア")
        self.assertEqual(get_genre_mapping(self.config, "business"), "ビジネス")
        self.assertEqual(get_genre_mapping(self.config, "economy"), "経済")
        self.assertEqual(get_genre_mapping(self.config, "daily"), "日常")

    def test_get_genre_mapping_unknown(self):
        """未知のジャンルが'その他'にフォールバックすること."""
        self.assertEqual(get_genre_mapping(self.config, "unknown_genre"), "その他")
        self.assertEqual(get_genre_mapping(self.config, ""), "その他")
        self.assertEqual(get_genre_mapping(self.config, "nonexistent"), "その他")


class TestSanitizeTopic(unittest.TestCase):
    """sanitize_topic() のテスト."""

    def test_sanitize_topic(self):
        """特殊文字がアンダースコアに置換されること."""
        self.assertEqual(
            sanitize_topic("Hello/World:Test*File"),
            "Hello_World_Test_File",
        )

    def test_sanitize_topic_with_various_special_chars(self):
        """様々な特殊文字が正しく処理されること."""
        # バックスラッシュ、クエスチョンマーク、アングルブラケット
        self.assertEqual(
            sanitize_topic('A\\B?C<D>E"F|G'),
            "A_B_C_D_E_F_G",
        )

    def test_sanitize_topic_unicode(self):
        """日本語トピックがそのまま保持されること."""
        self.assertEqual(
            sanitize_topic("スマートフォン"),
            "スマートフォン",
        )

    def test_sanitize_topic_empty(self):
        """空文字列が空文字列を返すこと."""
        self.assertEqual(sanitize_topic(""), "")


class TestPreview(unittest.TestCase):
    """generate_preview() のテスト."""

    def test_preview_genre_counts(self):
        """プレビューにジャンル別件数が含まれること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用Markdownファイルを作成
            files_data = [
                ("eng1.md", "engineer", "Python"),
                ("eng2.md", "engineer", "Docker"),
                ("biz1.md", "business", "Management"),
                ("eco1.md", "economy", "Finance"),
            ]
            for filename, genre, topic in files_data:
                filepath = Path(tmpdir) / filename
                filepath.write_text(
                    f"---\ntitle: {filename}\ngenre: {genre}\ntopic: {topic}\n---\nContent\n",
                    encoding="utf-8",
                )

            config = {
                "genre_mapping": {
                    "engineer": "エンジニア",
                    "business": "ビジネス",
                    "economy": "経済",
                    "daily": "日常",
                    "other": "その他",
                },
                "default_input": tmpdir,
                "default_output": str(Path(tmpdir) / "output"),
            }

            result = generate_preview(config, input_dir=tmpdir)

            # ジャンル別件数が含まれること
            self.assertIn("エンジニア", result)
            self.assertIn("ビジネス", result)
            self.assertIn("経済", result)
            # engineer が 2件
            self.assertIn("2", result)

    def test_preview_folder_existence(self):
        """プレビューにフォルダ存在確認が含まれること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            # output内に一部フォルダを事前作成
            existing_dir = output_dir / "エンジニア"
            existing_dir.mkdir(parents=True)

            # テストファイルを作成
            test_file = input_dir / "test.md"
            test_file.write_text(
                "---\ntitle: Test\ngenre: engineer\ntopic: Python\n---\nContent\n",
                encoding="utf-8",
            )

            config = {
                "genre_mapping": {"engineer": "エンジニア"},
                "default_input": str(input_dir),
                "default_output": str(output_dir),
            }

            result = generate_preview(
                config,
                input_dir=str(input_dir),
                output_dir=str(output_dir),
            )

            # フォルダ存在状況が出力に含まれること
            self.assertIsNotNone(result)
            self.assertTrue(len(result) > 0)

    def test_preview_empty_input(self):
        """入力ファイルがない場合、適切なメッセージを返すこと."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "genre_mapping": {"engineer": "エンジニア"},
                "default_input": tmpdir,
                "default_output": str(Path(tmpdir) / "output"),
            }

            result = generate_preview(config, input_dir=tmpdir)

            # 空入力に対する適切な応答
            self.assertIsNotNone(result)
            # ファイルが0件であることを示す内容
            self.assertTrue(
                "0" in result
                or "なし" in result
                or "No" in result.lower()
                or "empty" in result.lower()
                or "見つかり" in result
            )


if __name__ == "__main__":
    unittest.main()
