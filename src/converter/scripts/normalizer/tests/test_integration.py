"""
test_integration.py - 統合テスト（@test → @session 検証）

テスト結果は @session/test/YYYYMMDD_HHMMSS/ に保存される。
通常動作時は test/ サブディレクトリのセッションは無視される。
"""
from __future__ import annotations

import json
import os
import unittest
from datetime import datetime
from pathlib import Path

# モジュールレベルのセッションディレクトリ（全テストで共有）
_session_dir: Path | None = None


def setUpModule():
    """モジュール開始時に1つのセッションを作成"""
    global _session_dir

    test_index_dir = os.environ.get("NORMALIZER_INDEX_DIR")
    if not test_index_dir:
        return

    from normalizer.config import SESSION_DIR

    # 新構造: test/YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _session_dir = SESSION_DIR / "test" / timestamp
    _session_dir.mkdir(parents=True, exist_ok=True)


class TestIntegration(unittest.TestCase):
    """統合テスト（@test → @session）"""

    @classmethod
    def setUpClass(cls):
        """テストクラス開始時のセットアップ"""
        cls.test_index_dir = os.environ.get("NORMALIZER_INDEX_DIR")
        if not cls.test_index_dir:
            raise unittest.SkipTest("NORMALIZER_INDEX_DIR not set")

        cls.test_index_path = Path(cls.test_index_dir)
        if not cls.test_index_path.exists():
            raise unittest.SkipTest(f"@test directory not found: {cls.test_index_dir}")

        cls.session_dir = _session_dir

    def setUp(self):
        """各テスト前のセットアップ"""
        from normalizer.state.manager import StateManager
        StateManager._instance = None

    def tearDown(self):
        """各テスト後のクリーンアップ"""
        from normalizer.state.manager import StateManager
        StateManager._instance = None

    def test_01_test_directory_exists(self):
        """@test ディレクトリが存在する"""
        self.assertTrue(self.test_index_path.exists())

    def test_02_fixtures_copied(self):
        """フィクスチャファイルがコピーされている"""
        expected = ["english_doc.md", "japanese_doc.md", "mixed_content.md",
                    "with_frontmatter.md", "without_frontmatter.md"]
        for f in expected:
            self.assertTrue((self.test_index_path / f).exists(), f"Missing: {f}")

    def test_03_session_initialization(self):
        """セッション初期化と状態ファイル作成"""
        from normalizer.state.manager import create_initial_state, get_state, save_state

        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        files = list(self.test_index_path.glob("*.md"))
        state = create_initial_state(files)
        save_state(state)

        # 全ファイルが作成されている
        self.assertTrue((self.session_dir / "session.json").exists())
        self.assertTrue((self.session_dir / "pending.json").exists())
        self.assertTrue((self.session_dir / "processed.json").exists())
        self.assertTrue((self.session_dir / "errors.json").exists())

        # session.json の内容検証
        data = json.loads((self.session_dir / "session.json").read_text(encoding="utf-8"))
        self.assertIn("session_id", data)
        self.assertIn("total_files", data)
        self.assertEqual(data["total_files"], len(files))

        # pending.json の内容検証
        pending = json.loads((self.session_dir / "pending.json").read_text(encoding="utf-8"))
        self.assertEqual(len(pending), len(files))

    def test_04_state_update_success(self):
        """成功結果で状態を更新"""
        from normalizer.state.manager import (
            create_initial_state, get_state, save_state, update_state
        )

        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        files = list(self.test_index_path.glob("*.md"))
        state = create_initial_state(files)

        result = {
            "file": files[0].name,
            "success": True,
            "destination": f"/dest/{files[0].name}",
            "error": None,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

        state = update_state(state, result)
        save_state(state)

        data = json.loads((self.session_dir / "processed.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[-1]["status"], "success")

    def test_05_state_update_error(self):
        """エラー結果で状態を更新"""
        from normalizer.state.manager import (
            create_initial_state, get_state, save_state, update_state
        )

        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        files = list(self.test_index_path.glob("*.md"))
        state = create_initial_state(files)

        result = {
            "file": files[1].name if len(files) > 1 else files[0].name,
            "success": False,
            "destination": None,
            "error": "Test error message",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

        state = update_state(state, result)
        save_state(state)

        data = json.loads((self.session_dir / "errors.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[-1]["error"], "Test error message")

    def test_06_full_lifecycle(self):
        """セッションの完全なライフサイクル"""
        from normalizer.state.manager import (
            create_initial_state, get_state, save_state, update_state
        )

        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        files = list(self.test_index_path.glob("*.md"))
        state = create_initial_state(files)
        save_state(state)

        # 全ファイル処理（シミュレート）
        for i, file in enumerate(files):
            result = {
                "file": file.name,
                "success": i % 2 == 0,
                "destination": f"/dest/{file.name}" if i % 2 == 0 else None,
                "error": None if i % 2 == 0 else f"Error processing {file.name}",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            state = update_state(state, result)
            save_state(state)

        # 検証
        self.assertEqual(len(state["pending"]), 0)
        self.assertEqual(len(state["processed"]), len(files))

        # ファイルから再読み込みして検証
        processed = json.loads(
            (self.session_dir / "processed.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(processed), len(files))


class TestFileIdE2E(unittest.TestCase):
    """file_id 機能の E2E テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス開始時のセットアップ"""
        cls.test_index_dir = os.environ.get("NORMALIZER_INDEX_DIR")
        if not cls.test_index_dir:
            raise unittest.SkipTest("NORMALIZER_INDEX_DIR not set")

        cls.test_index_path = Path(cls.test_index_dir)
        if not cls.test_index_path.exists():
            raise unittest.SkipTest(f"@test directory not found: {cls.test_index_dir}")

        cls.session_dir = _session_dir

    def test_07_file_id_generation_for_file_without_id(self):
        """file_id がないファイルに file_id が生成される"""
        from normalizer.processing.single import (
            extract_file_id_from_frontmatter,
            get_or_generate_file_id,
        )

        # without_frontmatter.md を読み込み
        test_file = self.test_index_path / "without_frontmatter.md"
        if not test_file.exists():
            self.skipTest(f"Test file not found: {test_file}")

        content = test_file.read_text(encoding="utf-8")

        # 既存の file_id がないことを確認
        existing_id = extract_file_id_from_frontmatter(content)
        self.assertIsNone(existing_id, "File should not have existing file_id")

        # file_id が生成されることを確認
        file_id = get_or_generate_file_id(content, test_file)
        self.assertIsNotNone(file_id, "file_id should be generated")
        self.assertEqual(len(file_id), 12, "file_id should be 12 characters")
        self.assertTrue(
            all(c in "0123456789abcdef" for c in file_id),
            "file_id should be hexadecimal"
        )

    def test_08_file_id_preservation_for_file_with_id(self):
        """既存の file_id が維持される"""
        from normalizer.processing.single import (
            extract_file_id_from_frontmatter,
            get_or_generate_file_id,
        )

        # with_file_id.md を読み込み
        test_file = self.test_index_path / "with_file_id.md"
        if not test_file.exists():
            self.skipTest(f"Test file not found: {test_file}")

        content = test_file.read_text(encoding="utf-8")

        # 既存の file_id を確認
        existing_id = extract_file_id_from_frontmatter(content)
        self.assertEqual(existing_id, "abc123def456", "File should have existing file_id")

        # get_or_generate_file_id が既存の ID を返すことを確認
        file_id = get_or_generate_file_id(content, test_file)
        self.assertEqual(file_id, "abc123def456", "Existing file_id should be preserved")

    def test_09_file_id_deterministic(self):
        """同じファイルに対して同じ file_id が生成される"""
        from normalizer.processing.single import get_or_generate_file_id

        # without_frontmatter.md を読み込み
        test_file = self.test_index_path / "without_frontmatter.md"
        if not test_file.exists():
            self.skipTest(f"Test file not found: {test_file}")

        content = test_file.read_text(encoding="utf-8")

        # 2回生成して同じ値になることを確認
        file_id_1 = get_or_generate_file_id(content, test_file)
        file_id_2 = get_or_generate_file_id(content, test_file)
        self.assertEqual(file_id_1, file_id_2, "file_id should be deterministic")

    def test_10_file_id_different_for_different_content(self):
        """異なるコンテンツには異なる file_id が生成される"""
        from normalizer.processing.single import get_or_generate_file_id

        test_file_1 = self.test_index_path / "english_doc.md"
        test_file_2 = self.test_index_path / "japanese_doc.md"

        if not test_file_1.exists() or not test_file_2.exists():
            self.skipTest("Test files not found")

        content_1 = test_file_1.read_text(encoding="utf-8")
        content_2 = test_file_2.read_text(encoding="utf-8")

        file_id_1 = get_or_generate_file_id(content_1, test_file_1)
        file_id_2 = get_or_generate_file_id(content_2, test_file_2)

        self.assertNotEqual(file_id_1, file_id_2, "Different files should have different file_ids")


if __name__ == "__main__":
    unittest.main()
