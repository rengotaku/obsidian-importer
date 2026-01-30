"""
test_files.py - ファイル操作モジュールのテスト

normalizer.io.files モジュールの関数をテスト
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from normalizer.tests import temp_index_dir, get_fixture_path, read_fixture


class TestReadFileContent(unittest.TestCase):
    """read_file_content 関数のテスト"""

    def test_read_with_frontmatter(self):
        """frontmatter付きファイルの読み込み - frontmatter以降が返される"""
        from normalizer.io.files import read_file_content

        fixture_path = get_fixture_path("with_frontmatter.md")
        content, error = read_file_content(fixture_path)

        self.assertIsNone(error)
        self.assertIn("サンプル本文", content)
        # frontmatter 部分は除去されている
        self.assertNotIn("title:", content)

    def test_read_without_frontmatter(self):
        """frontmatterなしファイルの読み込み"""
        from normalizer.io.files import read_file_content

        fixture_path = get_fixture_path("without_frontmatter.md")
        content, error = read_file_content(fixture_path)

        self.assertIsNone(error)
        self.assertIn("タイトルなしドキュメント", content)

    def test_read_nonexistent_file(self):
        """存在しないファイルの読み込み - エラーメッセージが返される"""
        from normalizer.io.files import read_file_content

        content, error = read_file_content(Path("/nonexistent/file.md"))

        self.assertEqual(content, "")
        self.assertIsNotNone(error)
        self.assertIn("ファイルが見つかりません", error)

    def test_read_with_max_chars(self):
        """max_chars 指定での切り詰め"""
        from normalizer.io.files import read_file_content

        fixture_path = get_fixture_path("english_doc.md")
        content, error = read_file_content(fixture_path, max_chars=50)

        self.assertIsNone(error)
        self.assertLessEqual(len(content), 50)


class TestWriteFileContent(unittest.TestCase):
    """write_file_content 関数のテスト"""

    def test_write_new_file(self):
        """新規ファイルへの書き込み"""
        from normalizer.io.files import write_file_content

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            content = "# Test\n\nTest content"

            error = write_file_content(filepath, content)

            self.assertIsNone(error)
            self.assertTrue(filepath.exists())
            self.assertEqual(filepath.read_text(encoding="utf-8"), content)

    def test_write_creates_parent_dirs(self):
        """親ディレクトリが自動作成される"""
        from normalizer.io.files import write_file_content

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "test.md"
            content = "Nested content"

            error = write_file_content(filepath, content)

            self.assertIsNone(error)
            self.assertTrue(filepath.exists())

    def test_write_overwrite_existing(self):
        """既存ファイルの上書き"""
        from normalizer.io.files import write_file_content

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            filepath.write_text("Old content", encoding="utf-8")

            error = write_file_content(filepath, "New content")

            self.assertIsNone(error)
            self.assertEqual(filepath.read_text(encoding="utf-8"), "New content")


class TestListIndexFiles(unittest.TestCase):
    """list_index_files 関数のテスト"""

    def test_list_empty_dir(self):
        """空ディレクトリでは空リストが返る"""
        # 環境変数経由で一時ディレクトリに切り替え
        with temp_index_dir() as index_dir:
            # config モジュールを再読み込みして INDEX_DIR を更新
            import importlib
            import normalizer.config
            importlib.reload(normalizer.config)

            # io.files も再読み込み（INDEX_DIR を使っているため）
            import normalizer.io.files
            importlib.reload(normalizer.io.files)

            from normalizer.io.files import list_index_files

            files = list_index_files()
            self.assertEqual(files, [])

    def test_list_with_md_files(self):
        """MDファイルがリストされる"""
        with temp_index_dir() as index_dir:
            # テストファイルを作成
            (index_dir / "test1.md").write_text("# Test 1", encoding="utf-8")
            (index_dir / "test2.md").write_text("# Test 2", encoding="utf-8")

            import importlib
            import normalizer.config
            importlib.reload(normalizer.config)
            import normalizer.io.files
            importlib.reload(normalizer.io.files)

            from normalizer.io.files import list_index_files

            files = list_index_files()
            self.assertEqual(len(files), 2)

    def test_list_excludes_hidden_folders(self):
        """隠しフォルダ内のファイルは除外"""
        with temp_index_dir() as index_dir:
            # 通常ファイル
            (index_dir / "visible.md").write_text("# Visible", encoding="utf-8")
            # 隠しフォルダ内ファイル
            hidden_dir = index_dir / ".hidden"
            hidden_dir.mkdir()
            (hidden_dir / "hidden.md").write_text("# Hidden", encoding="utf-8")

            import importlib
            import normalizer.config
            importlib.reload(normalizer.config)
            import normalizer.io.files
            importlib.reload(normalizer.io.files)

            from normalizer.io.files import list_index_files

            files = list_index_files()
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "visible.md")

    def test_list_excludes_result_files(self):
        """処理結果ファイルは除外"""
        with temp_index_dir() as index_dir:
            (index_dir / "normal.md").write_text("# Normal", encoding="utf-8")
            (index_dir / "処理結果_20240101.md").write_text("# Result", encoding="utf-8")

            import importlib
            import normalizer.config
            importlib.reload(normalizer.config)
            import normalizer.io.files
            importlib.reload(normalizer.io.files)

            from normalizer.io.files import list_index_files

            files = list_index_files()
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "normal.md")


class TestGetDestinationPath(unittest.TestCase):
    """get_destination_path 関数のテスト"""

    def test_destination_for_genre(self):
        """ジャンルに対応するパスが返る"""
        from normalizer.io.files import get_destination_path
        from normalizer.config import VAULT_MAP

        dest = get_destination_path("エンジニア", "test.md")
        expected_base = VAULT_MAP["エンジニア"]
        self.assertEqual(dest.parent, expected_base)
        self.assertEqual(dest.name, "test.md")

    def test_destination_with_subfolder(self):
        """サブフォルダ指定で正しいパスが返る"""
        import shutil
        from normalizer.io.files import get_destination_path
        from normalizer.config import VAULT_MAP

        subfolder = "_test_subfolder_temp"
        dest = get_destination_path("エンジニア", "test.md", subfolder)
        expected_base = VAULT_MAP["エンジニア"] / subfolder

        self.assertEqual(dest.parent, expected_base)
        self.assertEqual(dest.name, "test.md")

        # クリーンアップ
        if expected_base.exists():
            shutil.rmtree(expected_base)

    def test_destination_with_new_subfolder(self):
        """'新規: xxx' 形式でサブフォルダが作成される"""
        import shutil
        from normalizer.io.files import get_destination_path
        from normalizer.config import VAULT_MAP

        subfolder_name = "_test_new_subfolder"
        dest = get_destination_path("エンジニア", "test.md", f"新規: {subfolder_name}")
        expected_base = VAULT_MAP["エンジニア"] / subfolder_name

        self.assertEqual(dest.parent, expected_base)
        self.assertTrue(expected_base.exists(), "サブフォルダが作成されていない")

        # クリーンアップ
        shutil.rmtree(expected_base)

    def test_destination_with_new_subfolder_fullwidth_colon(self):
        """'新規：xxx' (全角コロン) 形式でもサブフォルダが作成される"""
        import shutil
        from normalizer.io.files import get_destination_path
        from normalizer.config import VAULT_MAP

        subfolder_name = "_test_new_subfolder_fw"
        dest = get_destination_path("エンジニア", "test.md", f"新規：{subfolder_name}")
        expected_base = VAULT_MAP["エンジニア"] / subfolder_name

        self.assertEqual(dest.parent, expected_base)
        self.assertTrue(expected_base.exists(), "サブフォルダが作成されていない")

        # クリーンアップ
        shutil.rmtree(expected_base)


if __name__ == "__main__":
    unittest.main()
