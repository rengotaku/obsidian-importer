"""
folder_manager モジュールのテスト
"""

import tempfile
import unittest
from pathlib import Path

from scripts.llm_import.common.folder_manager import FolderManager


class TestFolderManager(unittest.TestCase):
    """FolderManager クラスのテスト"""

    def test_get_session_dir_import(self):
        """import タイプのセッションディレクトリパスが正しいことを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            session_dir = manager.get_session_dir("import", "20260117_150000")

            expected = base_path / "import" / "20260117_150000"
            self.assertEqual(session_dir, expected)

    def test_get_session_dir_organize(self):
        """organize タイプのセッションディレクトリパスが正しいことを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            session_dir = manager.get_session_dir("organize", "20260117_150000")

            expected = base_path / "organize" / "20260117_150000"
            self.assertEqual(session_dir, expected)

    def test_get_session_dir_test(self):
        """test タイプのセッションディレクトリパスが正しいことを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            session_dir = manager.get_session_dir("test", "20260117_150000")

            expected = base_path / "test" / "20260117_150000"
            self.assertEqual(session_dir, expected)

    def test_create_session_structure_import(self):
        """import タイプのセッション構造が正しく作成されることを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            paths = manager.create_session_structure("import", "20260117_150000")

            # セッションディレクトリが作成されたことを確認
            self.assertTrue(paths["session"].exists())
            self.assertEqual(paths["session"].name, "20260117_150000")

            # サブフォルダが作成されたことを確認
            self.assertTrue(paths["parsed"].exists())
            self.assertTrue(paths["output"].exists())
            self.assertTrue(paths["errors"].exists())

            # パスが正しいことを確認
            self.assertEqual(
                paths["parsed"],
                base_path / "import" / "20260117_150000" / "parsed" / "conversations",
            )
            self.assertEqual(
                paths["output"], base_path / "import" / "20260117_150000" / "output"
            )
            self.assertEqual(
                paths["errors"], base_path / "import" / "20260117_150000" / "errors"
            )

    def test_create_session_structure_organize(self):
        """organize タイプのセッション構造が正しく作成されることを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            paths = manager.create_session_structure("organize", "20260117_150000")

            # セッションディレクトリのみが作成されることを確認
            self.assertTrue(paths["session"].exists())
            self.assertEqual(len(paths), 1)  # session のみ

    def test_create_session_structure_test(self):
        """test タイプのセッション構造が正しく作成されることを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            manager = FolderManager(base_path)

            paths = manager.create_session_structure("test", "20260117_150000")

            # セッションディレクトリのみが作成されることを確認
            self.assertTrue(paths["session"].exists())
            self.assertEqual(len(paths), 1)  # session のみ


if __name__ == "__main__":
    unittest.main()
