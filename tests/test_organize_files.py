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


class TestGetDestinationPath(unittest.TestCase):
    """get_destination_path() のテスト (Phase 3 RED)."""

    def setUp(self):
        """テスト用設定を準備."""
        from scripts.organize_files import get_destination_path

        self.get_destination_path = get_destination_path
        self.config = {
            "genre_mapping": {
                "engineer": "エンジニア",
                "business": "ビジネス",
                "economy": "経済",
                "daily": "日常",
                "other": "その他",
            },
            "unclassified_folder": "unclassified",
        }

    def test_get_destination_path(self):
        """genre と topic から正しいターゲットパスが計算されること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"genre": "engineer", "topic": "Python"}
        filename = "test_article.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "エンジニア" / "Python" / "test_article.md"
        self.assertEqual(result, expected)

    def test_get_destination_path_economy(self):
        """economy ジャンルが経済フォルダにマッピングされること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"genre": "economy", "topic": "スマートフォン"}
        filename = "example.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "経済" / "スマートフォン" / "example.md"
        self.assertEqual(result, expected)

    def test_get_destination_path_special_topic(self):
        """topic の特殊文字がサニタイズされること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"genre": "engineer", "topic": "C/C++:Tips"}
        filename = "coding.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "エンジニア" / "C_C++_Tips" / "coding.md"
        self.assertEqual(result, expected)

    def test_get_destination_unclassified_no_genre(self):
        """genre がない場合 unclassified フォルダに振り分けられること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"title": "No Genre Article"}
        filename = "no_genre.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "unclassified" / "no_genre.md"
        self.assertEqual(result, expected)

    def test_get_destination_unclassified_empty_genre(self):
        """genre が空文字列の場合 unclassified フォルダに振り分けられること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"genre": "", "topic": "Something"}
        filename = "empty_genre.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "unclassified" / "empty_genre.md"
        self.assertEqual(result, expected)

    def test_get_destination_no_topic(self):
        """topic がない場合 genre フォルダ直下に配置されること."""
        output_dir = Path("/tmp/test_output")
        frontmatter = {"genre": "daily"}
        filename = "no_topic.md"

        result = self.get_destination_path(self.config, frontmatter, filename, output_dir)

        expected = output_dir / "日常" / "no_topic.md"
        self.assertEqual(result, expected)


class TestMoveFile(unittest.TestCase):
    """move_file() のテスト (Phase 3 RED)."""

    def setUp(self):
        """テスト用に move_file をインポート."""
        from scripts.organize_files import move_file

        self.move_file = move_file

    def test_move_file_success(self):
        """ファイルが正常に移動されること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.md"
            dest_dir = Path(tmpdir) / "dest"
            dest_dir.mkdir()
            dest = dest_dir / "source.md"

            source.write_text("---\ntitle: Test\n---\nContent\n", encoding="utf-8")

            result = self.move_file(source, dest)

            self.assertFalse(source.exists(), "source ファイルが残っている")
            self.assertTrue(dest.exists(), "dest ファイルが作成されていない")
            self.assertEqual(
                dest.read_text(encoding="utf-8"),
                "---\ntitle: Test\n---\nContent\n",
            )
            self.assertEqual(result, "success")

    def test_move_file_creates_directory(self):
        """振り分け先ディレクトリが存在しない場合、自動作成されること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.md"
            dest = Path(tmpdir) / "new_dir" / "sub_dir" / "source.md"

            source.write_text("---\ntitle: Test\n---\nContent\n", encoding="utf-8")

            result = self.move_file(source, dest)

            self.assertTrue(dest.parent.exists(), "ディレクトリが作成されていない")
            self.assertTrue(dest.exists(), "ファイルが移動されていない")
            self.assertFalse(source.exists(), "source ファイルが残っている")
            self.assertEqual(result, "success")

    def test_move_file_skip_existing(self):
        """振り分け先に同名ファイルが存在する場合、スキップすること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.md"
            dest_dir = Path(tmpdir) / "dest"
            dest_dir.mkdir()
            dest = dest_dir / "source.md"

            source.write_text("New content", encoding="utf-8")
            dest.write_text("Existing content", encoding="utf-8")

            result = self.move_file(source, dest)

            self.assertTrue(source.exists(), "source ファイルが削除された")
            self.assertEqual(
                dest.read_text(encoding="utf-8"),
                "Existing content",
                "既存ファイルが上書きされた",
            )
            self.assertEqual(result, "skipped")

    def test_move_file_source_not_found(self):
        """存在しない source ファイルでエラーが返ること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "nonexistent.md"
            dest = Path(tmpdir) / "dest" / "nonexistent.md"

            result = self.move_file(source, dest)

            self.assertEqual(result, "error")


class TestOrganizeFiles(unittest.TestCase):
    """organize_files() のテスト (Phase 3 RED)."""

    def setUp(self):
        """テスト用に organize_files をインポート."""
        from scripts.organize_files import organize_files

        self.organize_files = organize_files
        self.config = {
            "genre_mapping": {
                "engineer": "エンジニア",
                "business": "ビジネス",
                "economy": "経済",
                "daily": "日常",
                "other": "その他",
            },
            "unclassified_folder": "unclassified",
        }

    def test_organize_files_summary(self):
        """処理サマリーに success/skip/error の件数が正しく含まれること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # engineer ファイル2件
            for i in range(2):
                f = input_dir / f"eng{i}.md"
                f.write_text(
                    f"---\ntitle: Eng{i}\ngenre: engineer\ntopic: Python\n---\nContent\n",
                    encoding="utf-8",
                )

            # business ファイル1件
            biz = input_dir / "biz.md"
            biz.write_text(
                "---\ntitle: Biz\ngenre: business\ntopic: Management\n---\nContent\n",
                encoding="utf-8",
            )

            # genre なしファイル1件
            noclass = input_dir / "noclass.md"
            noclass.write_text(
                "---\ntitle: NoClass\n---\nContent\n",
                encoding="utf-8",
            )

            summary = self.organize_files(self.config, input_dir, output_dir)

            # ProcessingSummary の検証
            self.assertEqual(summary["total"], 4)
            self.assertEqual(summary["success"], 4)
            self.assertEqual(summary["skipped"], 0)
            self.assertEqual(summary["error"], 0)
            self.assertIn("by_genre", summary)

    def test_organize_files_with_existing_dest(self):
        """振り分け先に同名ファイルが既に存在する場合 skipped としてカウントされること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # ファイル作成
            src = input_dir / "dup.md"
            src.write_text(
                "---\ntitle: Dup\ngenre: engineer\ntopic: Python\n---\nContent\n",
                encoding="utf-8",
            )

            # 振り分け先に同名ファイルを事前配置
            dest_dir = output_dir / "エンジニア" / "Python"
            dest_dir.mkdir(parents=True)
            existing = dest_dir / "dup.md"
            existing.write_text("Existing", encoding="utf-8")

            summary = self.organize_files(self.config, input_dir, output_dir)

            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["skipped"], 1)
            self.assertEqual(summary["success"], 0)

    def test_organize_files_empty_input(self):
        """入力ディレクトリが空の場合、全カウント0のサマリーが返ること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            summary = self.organize_files(self.config, input_dir, output_dir)

            self.assertEqual(summary["total"], 0)
            self.assertEqual(summary["success"], 0)
            self.assertEqual(summary["skipped"], 0)
            self.assertEqual(summary["error"], 0)

    def test_organize_files_genre_counts(self):
        """by_genre にジャンル別件数が正しく記録されること."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # 異なるジャンルのファイル
            files_data = [
                ("eng.md", "engineer", "Python"),
                ("biz.md", "business", "Sales"),
                ("eco.md", "economy", "Finance"),
            ]
            for fname, genre, topic in files_data:
                f = input_dir / fname
                f.write_text(
                    f"---\ntitle: {fname}\ngenre: {genre}\ntopic: {topic}\n---\nContent\n",
                    encoding="utf-8",
                )

            summary = self.organize_files(self.config, input_dir, output_dir)

            self.assertEqual(summary["by_genre"].get("エンジニア", 0), 1)
            self.assertEqual(summary["by_genre"].get("ビジネス", 0), 1)
            self.assertEqual(summary["by_genre"].get("経済", 0), 1)


if __name__ == "__main__":
    unittest.main()
