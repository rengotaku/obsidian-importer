"""
test_session.py - セッション・状態管理モジュールのテスト

normalizer.state.manager および normalizer.io.session モジュールのテスト
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class TestStateManagerSingleton(unittest.TestCase):
    """StateManager シングルトンのテスト"""

    def tearDown(self):
        """各テスト後にStateManagerをリセット"""
        from normalizer.state.manager import StateManager
        StateManager._instance = None

    def test_singleton_pattern(self):
        """同じインスタンスが返される"""
        from normalizer.state.manager import StateManager, get_state

        mgr1 = StateManager()
        mgr2 = get_state()

        self.assertIs(mgr1, mgr2)

    def test_initial_state(self):
        """初期状態の確認"""
        from normalizer.state.manager import get_state

        mgr = get_state()

        self.assertIsNone(mgr.session_dir)
        self.assertIsNone(mgr.cached_prompt)
        self.assertFalse(mgr.stage_debug_mode)
        self.assertEqual(mgr.excluded_files, [])

    def test_reset(self):
        """reset() で状態がクリアされる"""
        from normalizer.state.manager import get_state

        mgr = get_state()
        mgr.session_dir = Path("/tmp/test")
        mgr.cached_prompt = "test prompt"

        mgr.reset()

        self.assertIsNone(mgr.session_dir)
        self.assertIsNone(mgr.cached_prompt)

    def test_set_session_dir(self):
        """set_session_dir でセッションディレクトリが設定される"""
        from normalizer.state.manager import get_state

        mgr = get_state()
        test_dir = Path("/tmp/test_session")

        mgr.set_session_dir(test_dir)

        self.assertEqual(mgr.session_dir, test_dir)


class TestCreateInitialState(unittest.TestCase):
    """create_initial_state 関数のテスト"""

    def test_create_with_files(self):
        """ファイルリストから初期状態を作成"""
        from normalizer.state.manager import create_initial_state

        files = [Path("/tmp/a.md"), Path("/tmp/b.md"), Path("/tmp/c.md")]
        state = create_initial_state(files)

        self.assertEqual(state["total_files"], 3)
        self.assertEqual(len(state["pending"]), 3)
        self.assertEqual(state["pending"], ["a.md", "b.md", "c.md"])
        self.assertEqual(state["processed"], [])
        self.assertEqual(state["errors"], [])
        self.assertIn("session_id", state)
        self.assertIn("started_at", state)

    def test_create_with_empty_list(self):
        """空のファイルリストで作成"""
        from normalizer.state.manager import create_initial_state

        state = create_initial_state([])

        self.assertEqual(state["total_files"], 0)
        self.assertEqual(state["pending"], [])


class TestUpdateState(unittest.TestCase):
    """update_state 関数のテスト"""

    def test_update_with_success_result(self):
        """成功結果で状態を更新"""
        from normalizer.state.manager import create_initial_state, update_state

        files = [Path("/tmp/test.md")]
        state = create_initial_state(files)

        result = {
            "file": "test.md",
            "success": True,
            "destination": "/tmp/dest/test.md",
            "error": None,
            "timestamp": "2024-01-15T10:00:00"
        }

        updated = update_state(state, result)

        self.assertEqual(len(updated["processed"]), 1)
        self.assertEqual(updated["processed"][0]["status"], "success")
        self.assertNotIn("test.md", updated["pending"])
        self.assertEqual(len(updated["errors"]), 0)

    def test_update_with_error_result(self):
        """エラー結果で状態を更新"""
        from normalizer.state.manager import create_initial_state, update_state

        files = [Path("/tmp/test.md")]
        state = create_initial_state(files)

        result = {
            "file": "test.md",
            "success": False,
            "destination": None,
            "error": "Processing failed",
            "timestamp": "2024-01-15T10:00:00"
        }

        updated = update_state(state, result)

        self.assertEqual(len(updated["processed"]), 1)
        self.assertEqual(updated["processed"][0]["status"], "error")
        self.assertEqual(len(updated["errors"]), 1)
        self.assertEqual(updated["errors"][0]["error"], "Processing failed")


class TestSessionFunctions(unittest.TestCase):
    """セッション関連関数のテスト"""

    def test_progress_bar(self):
        """プログレスバー生成"""
        from normalizer.io.session import progress_bar

        bar = progress_bar(5, 10, width=20)

        self.assertIn("[", bar)
        self.assertIn("]", bar)
        self.assertIn("5/10", bar)
        self.assertIn("50.0%", bar)

    def test_progress_bar_zero_total(self):
        """total=0 の場合"""
        from normalizer.io.session import progress_bar

        bar = progress_bar(0, 0, width=20)

        self.assertIn("0/0", bar)
        self.assertIn("0%", bar)

    def test_timestamp_format(self):
        """タイムスタンプ形式"""
        from normalizer.io.session import timestamp

        ts = timestamp()

        # ISO 8601 形式（秒まで）
        self.assertRegex(ts, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class TestStatePersistence(unittest.TestCase):
    """状態の永続化テスト"""

    def setUp(self):
        """テスト用一時ディレクトリを作成"""
        self.tmpdir = tempfile.mkdtemp()
        self.session_dir = Path(self.tmpdir) / "session"
        self.session_dir.mkdir()

        # StateManager をリセット
        from normalizer.state.manager import StateManager
        StateManager._instance = None

    def tearDown(self):
        """StateManager をリセット"""
        from normalizer.state.manager import StateManager
        StateManager._instance = None

        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_state(self):
        """状態の保存と読み込み"""
        from normalizer.state.manager import get_state, save_state, create_initial_state

        # セッションディレクトリを設定
        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        # 初期状態を作成して保存
        files = [Path("/tmp/file1.md"), Path("/tmp/file2.md")]
        state = create_initial_state(files)
        save_state(state)

        # ファイルが作成されているか確認
        self.assertTrue((self.session_dir / "session.json").exists())
        self.assertTrue((self.session_dir / "pending.json").exists())
        self.assertTrue((self.session_dir / "processed.json").exists())
        self.assertTrue((self.session_dir / "errors.json").exists())


class TestLogMessage(unittest.TestCase):
    """log_message 関数のテスト"""

    def setUp(self):
        """テスト用一時ディレクトリを作成"""
        self.tmpdir = tempfile.mkdtemp()
        self.session_dir = Path(self.tmpdir) / "session"
        self.session_dir.mkdir()

        from normalizer.state.manager import StateManager
        StateManager._instance = None

    def tearDown(self):
        from normalizer.state.manager import StateManager
        StateManager._instance = None

        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_log_with_session(self):
        """セッションありでのログ"""
        from normalizer.io.session import log_message, get_log_file
        from normalizer.state.manager import get_state

        mgr = get_state()
        mgr.set_session_dir(self.session_dir)

        log_message("Test message", self.session_dir, also_print=False)

        log_file = get_log_file(self.session_dir)
        self.assertTrue(log_file.exists())
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("Test message", content)

    def test_log_without_session(self):
        """セッションなしでのログ（エラーにならない）"""
        from normalizer.io.session import log_message

        # エラーなく実行されることを確認
        log_message("Test message", session_dir=None, also_print=False)


if __name__ == "__main__":
    unittest.main()
