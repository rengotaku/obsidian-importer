"""
リトライ機能のユニットテスト
"""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.llm_import.common.retry import (
    SessionInfo,
    ErrorEntry,
    find_session_dirs,
    load_errors_json,
    load_session_json,
    get_sessions_with_errors,
    validate_session,
    format_session_list,
    select_session_interactive,
    format_error_preview,
    preview_retry,
)


class TestSessionInfo(unittest.TestCase):
    """SessionInfo dataclass のテスト"""

    def test_creates_session_info(self):
        """SessionInfo が作成される"""
        info = SessionInfo(
            session_id="import_20260116_203426",
            error_count=21,
            updated_at="2026-01-17T00:37:01",
        )
        self.assertEqual(info.session_id, "import_20260116_203426")
        self.assertEqual(info.error_count, 21)
        self.assertEqual(info.updated_at, "2026-01-17T00:37:01")
        self.assertIsNone(info.source_session)

    def test_creates_session_info_with_source(self):
        """source_session 付きの SessionInfo が作成される"""
        info = SessionInfo(
            session_id="import_20260117_120000",
            error_count=3,
            updated_at="2026-01-17T12:30:00",
            source_session="import_20260116_203426",
        )
        self.assertEqual(info.source_session, "import_20260116_203426")

    def test_validates_session_id_required(self):
        """session_id は必須"""
        with self.assertRaises(ValueError) as cm:
            SessionInfo(session_id="", error_count=0, updated_at="2026-01-17")
        self.assertIn("session_id", str(cm.exception))

    def test_validates_error_count_non_negative(self):
        """error_count は 0 以上"""
        with self.assertRaises(ValueError) as cm:
            SessionInfo(session_id="test", error_count=-1, updated_at="2026-01-17")
        self.assertIn("error_count", str(cm.exception))


class TestErrorEntry(unittest.TestCase):
    """ErrorEntry dataclass のテスト"""

    def test_creates_error_entry(self):
        """ErrorEntry が作成される"""
        entry = ErrorEntry(
            file="fe26208b-dc85-48be-a01f-2e8fc98684b8",
            error="JSONパースエラー",
            stage="phase2",
            timestamp="2026-01-16T21:42:18",
        )
        self.assertEqual(entry.file, "fe26208b-dc85-48be-a01f-2e8fc98684b8")
        self.assertEqual(entry.error, "JSONパースエラー")
        self.assertEqual(entry.stage, "phase2")
        self.assertEqual(entry.timestamp, "2026-01-16T21:42:18")


class TestFindSessionDirs(unittest.TestCase):
    """find_session_dirs のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plan_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_returns_empty_for_nonexistent_dir(self):
        """存在しないディレクトリでは空リストを返す"""
        result = find_session_dirs(Path("/nonexistent/path"))
        self.assertEqual(result, [])

    def test_returns_empty_for_empty_dir(self):
        """空のディレクトリでは空リストを返す"""
        result = find_session_dirs(self.plan_dir)
        self.assertEqual(result, [])

    def test_finds_import_dirs_only(self):
        """import 関連ディレクトリのみ返す（新旧両構造対応）"""
        # 新構造: import/ サブディレクトリ
        import_subdir = self.plan_dir / "import"
        import_subdir.mkdir()
        (import_subdir / "20260118_100000").mkdir()
        (import_subdir / "20260118_120000").mkdir()
        # 旧構造: import_ プレフィックス
        (self.plan_dir / "import_20260116_203426").mkdir()
        (self.plan_dir / "import_20260117_120000").mkdir()
        # 他のディレクトリを作成（対象外）
        (self.plan_dir / "test").mkdir()  # 新構造の test/ は対象外
        (self.plan_dir / "test_20260114_163349").mkdir()  # 旧構造の test_ も対象外
        (self.plan_dir / "20260113_155514").mkdir()

        result = find_session_dirs(self.plan_dir)

        self.assertEqual(len(result), 4)
        names = [d.name for d in result]
        # 新構造
        self.assertIn("20260118_100000", names)
        self.assertIn("20260118_120000", names)
        # 旧構造
        self.assertIn("import_20260116_203426", names)
        self.assertIn("import_20260117_120000", names)
        # 除外されている
        self.assertNotIn("test_20260114_163349", names)
        self.assertNotIn("test", names)

    def test_sorts_by_mtime_descending(self):
        """更新日時の降順でソートされる"""
        import os
        import time

        # ディレクトリを作成して更新日時を設定
        dir1 = self.plan_dir / "import_20260116_100000"
        dir2 = self.plan_dir / "import_20260116_200000"
        dir1.mkdir()
        dir2.mkdir()

        # dir1 を古く、dir2 を新しく設定
        old_time = time.time() - 3600
        new_time = time.time()
        os.utime(dir1, (old_time, old_time))
        os.utime(dir2, (new_time, new_time))

        result = find_session_dirs(self.plan_dir)

        # 新しいものが先
        self.assertEqual(result[0].name, "import_20260116_200000")
        self.assertEqual(result[1].name, "import_20260116_100000")


class TestLoadErrorsJson(unittest.TestCase):
    """load_errors_json のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_raises_for_missing_file(self):
        """errors.json が存在しない場合は FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            load_errors_json(self.session_dir)

    def test_raises_for_invalid_json(self):
        """不正な JSON の場合は JSONDecodeError"""
        errors_file = self.session_dir / "errors.json"
        errors_file.write_text("invalid json", encoding="utf-8")

        with self.assertRaises(json.JSONDecodeError):
            load_errors_json(self.session_dir)

    def test_loads_valid_errors(self):
        """正常な errors.json を読み込む"""
        errors_data = [
            {
                "file": "fe26208b-dc85-48be-a01f-2e8fc98684b8",
                "error": "JSONパースエラー",
                "stage": "phase2",
                "timestamp": "2026-01-16T21:42:18",
            },
            {
                "file": "74fda9a1-8db3-49c6-a107-5b143bd09492",
                "error": "JSON形式の応答がありません",
                "stage": "phase2",
                "timestamp": "2026-01-16T21:48:25",
            },
        ]
        errors_file = self.session_dir / "errors.json"
        errors_file.write_text(json.dumps(errors_data), encoding="utf-8")

        result = load_errors_json(self.session_dir)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].file, "fe26208b-dc85-48be-a01f-2e8fc98684b8")
        self.assertEqual(result[0].error, "JSONパースエラー")
        self.assertEqual(result[1].file, "74fda9a1-8db3-49c6-a107-5b143bd09492")

    def test_handles_empty_array(self):
        """空の配列を読み込む"""
        errors_file = self.session_dir / "errors.json"
        errors_file.write_text("[]", encoding="utf-8")

        result = load_errors_json(self.session_dir)

        self.assertEqual(result, [])


class TestLoadSessionJson(unittest.TestCase):
    """load_session_json のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_raises_for_missing_file(self):
        """session.json が存在しない場合は FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            load_session_json(self.session_dir)

    def test_loads_valid_session(self):
        """正常な session.json を読み込む"""
        session_data = {
            "session_id": "import_20260116_203426",
            "started_at": "2026-01-16T20:34:26",
            "updated_at": "2026-01-17T00:37:01",
            "total_files": 422,
            "provider": "claude",
        }
        session_file = self.session_dir / "session.json"
        session_file.write_text(json.dumps(session_data), encoding="utf-8")

        result = load_session_json(self.session_dir)

        self.assertEqual(result["session_id"], "import_20260116_203426")
        self.assertEqual(result["provider"], "claude")


class TestGetSessionsWithErrors(unittest.TestCase):
    """get_sessions_with_errors のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plan_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_returns_empty_for_no_sessions(self):
        """セッションがない場合は空リスト"""
        result = get_sessions_with_errors(self.plan_dir)
        self.assertEqual(result, [])

    def test_returns_sessions_with_errors(self):
        """エラーを含むセッションのみ返す"""
        # エラーありセッション
        session1 = self.plan_dir / "import_20260116_203426"
        session1.mkdir()
        (session1 / "errors.json").write_text(
            json.dumps([{"file": "a", "error": "err", "stage": "phase2", "timestamp": "2026-01-16"}]),
            encoding="utf-8",
        )
        (session1 / "session.json").write_text(
            json.dumps({
                "session_id": "import_20260116_203426",
                "updated_at": "2026-01-17T00:37:01",
            }),
            encoding="utf-8",
        )

        # エラーなしセッション
        session2 = self.plan_dir / "import_20260117_100000"
        session2.mkdir()
        (session2 / "session.json").write_text(
            json.dumps({"session_id": "import_20260117_100000"}),
            encoding="utf-8",
        )

        result = get_sessions_with_errors(self.plan_dir)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].session_id, "import_20260116_203426")
        self.assertEqual(result[0].error_count, 1)

    def test_skips_empty_errors(self):
        """空の errors.json はスキップ"""
        session1 = self.plan_dir / "import_20260116_203426"
        session1.mkdir()
        (session1 / "errors.json").write_text("[]", encoding="utf-8")

        result = get_sessions_with_errors(self.plan_dir)

        self.assertEqual(result, [])


class TestValidateSession(unittest.TestCase):
    """validate_session のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plan_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_invalid_for_nonexistent_session(self):
        """存在しないセッションは invalid"""
        valid, message = validate_session("nonexistent", self.plan_dir)
        self.assertFalse(valid)
        self.assertIn("見つかりません", message)

    def test_invalid_for_no_errors_file(self):
        """errors.json がないセッションは invalid"""
        session = self.plan_dir / "import_20260116_203426"
        session.mkdir()

        valid, message = validate_session("import_20260116_203426", self.plan_dir)
        self.assertFalse(valid)
        self.assertIn("エラーファイルがありません", message)

    def test_invalid_for_empty_errors(self):
        """空の errors.json は invalid"""
        session = self.plan_dir / "import_20260116_203426"
        session.mkdir()
        (session / "errors.json").write_text("[]", encoding="utf-8")

        valid, message = validate_session("import_20260116_203426", self.plan_dir)
        self.assertFalse(valid)
        self.assertIn("エラーがありません", message)

    def test_valid_for_session_with_errors(self):
        """エラーのあるセッションは valid"""
        session = self.plan_dir / "import_20260116_203426"
        session.mkdir()
        (session / "errors.json").write_text(
            json.dumps([{"file": "a", "error": "err", "stage": "phase2", "timestamp": "2026-01-16"}]),
            encoding="utf-8",
        )

        valid, message = validate_session("import_20260116_203426", self.plan_dir)
        self.assertTrue(valid)
        self.assertIn("1 件", message)


class TestFormatSessionList(unittest.TestCase):
    """format_session_list のテスト"""

    def test_formats_empty_list(self):
        """空リストのフォーマット"""
        result = format_session_list([])
        self.assertIn("セッションがありません", result)

    def test_formats_single_session(self):
        """単一セッションのフォーマット"""
        sessions = [
            SessionInfo(
                session_id="import_20260116_203426",
                error_count=21,
                updated_at="2026-01-17T00:37:01",
            )
        ]
        result = format_session_list(sessions)

        self.assertIn("import_20260116_203426", result)
        self.assertIn("21", result)
        self.assertIn("2026-01-17 00:37", result)

    def test_formats_multiple_sessions(self):
        """複数セッションのフォーマット"""
        sessions = [
            SessionInfo(
                session_id="import_20260116_203426",
                error_count=21,
                updated_at="2026-01-17T00:37:01",
            ),
            SessionInfo(
                session_id="import_20260115_143210",
                error_count=5,
                updated_at="2026-01-15T18:22:00",
            ),
        ]
        result = format_session_list(sessions)

        self.assertIn("import_20260116_203426", result)
        self.assertIn("import_20260115_143210", result)
        self.assertIn("SESSION を指定して実行してください", result)


class TestSelectSessionInteractive(unittest.TestCase):
    """select_session_interactive のテスト"""

    def test_returns_none_for_empty(self):
        """空リストでは None"""
        result = select_session_interactive([])
        self.assertIsNone(result)

    def test_returns_single_session(self):
        """1件のみの場合は自動選択"""
        sessions = [
            SessionInfo(
                session_id="import_20260116_203426",
                error_count=21,
                updated_at="2026-01-17T00:37:01",
            )
        ]
        result = select_session_interactive(sessions)

        self.assertIsNotNone(result)
        self.assertEqual(result.session_id, "import_20260116_203426")

    def test_returns_none_for_multiple(self):
        """複数の場合は None"""
        sessions = [
            SessionInfo(session_id="a", error_count=1, updated_at="2026-01-17"),
            SessionInfo(session_id="b", error_count=2, updated_at="2026-01-16"),
        ]
        result = select_session_interactive(sessions)
        self.assertIsNone(result)


class TestFormatErrorPreview(unittest.TestCase):
    """format_error_preview のテスト"""

    def test_formats_empty_list(self):
        """空リストのフォーマット"""
        result = format_error_preview([])
        self.assertIn("エラーがありません", result)

    def test_formats_single_error(self):
        """単一エラーのフォーマット"""
        errors = [
            ErrorEntry(
                file="fe26208b-dc85-48be-a01f-2e8fc98684b8",
                error="JSONパースエラー",
                stage="phase2",
                timestamp="2026-01-16T21:42:18",
            )
        ]
        result = format_error_preview(errors)

        self.assertIn("fe26208b", result)
        self.assertIn("JSONパースエラー", result)
        self.assertIn("合計: 1 件", result)
        self.assertIn("[プレビューモード]", result)

    def test_truncates_long_error(self):
        """長いエラーメッセージは切り詰め"""
        errors = [
            ErrorEntry(
                file="a" * 36,
                error="A" * 100,
                stage="phase2",
                timestamp="2026-01-16T21:42:18",
            )
        ]
        result = format_error_preview(errors)

        # 30文字 + "..."
        self.assertIn("...", result)


class TestPreviewRetry(unittest.TestCase):
    """preview_retry のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plan_dir = Path(self.temp_dir)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_returns_error_for_missing_session(self):
        """存在しないセッションでエラーメッセージ"""
        result = preview_retry("nonexistent", self.plan_dir)
        self.assertIn("❌", result)

    def test_returns_preview_for_valid_session(self):
        """有効なセッションでプレビュー表示"""
        session = self.plan_dir / "import_20260116_203426"
        session.mkdir()
        (session / "errors.json").write_text(
            json.dumps([
                {
                    "file": "fe26208b-dc85-48be-a01f-2e8fc98684b8",
                    "error": "JSONパースエラー",
                    "stage": "phase2",
                    "timestamp": "2026-01-16T21:42:18",
                }
            ]),
            encoding="utf-8",
        )

        result = preview_retry("import_20260116_203426", self.plan_dir)

        self.assertIn("fe26208b", result)
        self.assertIn("JSONパースエラー", result)
        self.assertIn("合計: 1 件", result)


if __name__ == "__main__":
    unittest.main()
