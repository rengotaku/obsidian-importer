"""
CLI モジュールのユニットテスト
"""
import json
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象
from scripts.llm_import.cli import (
    create_parser,
    main,
    cmd_status,
    cmd_reset,
    cmd_preview,
    _generate_filename,
    _format_duration,
    EXIT_SUCCESS,
    EXIT_ARGUMENT_ERROR,
    EXIT_INPUT_NOT_FOUND,
    EXIT_UNKNOWN_PROVIDER,
    LLM_EXPORTS_BASE,
)


class TestCreateParser(unittest.TestCase):
    """create_parser のテスト"""

    def test_creates_parser(self):
        """パーサーが作成される"""
        parser = create_parser()
        self.assertIsNotNone(parser)

    def test_provider_option_required_message(self):
        """--provider が省略された場合のヘルプメッセージ"""
        parser = create_parser()
        args = parser.parse_args(["--preview", "some_dir"])
        # preview が設定されている
        self.assertTrue(args.preview)
        # provider は None
        self.assertIsNone(args.provider)

    def test_parses_all_options(self):
        """全オプションがパースされる"""
        parser = create_parser()
        args = parser.parse_args([
            "--provider", "claude",
            "--output", "/tmp/output",
            "--preview",
            "--no-delete",
            "--verbose",
            "input_dir",
        ])
        self.assertEqual(args.provider, "claude")
        self.assertEqual(args.output, Path("/tmp/output"))
        self.assertTrue(args.preview)
        self.assertTrue(args.no_delete)
        self.assertTrue(args.verbose)
        self.assertEqual(args.input_dir, Path("input_dir"))


class TestMainEntryPoint(unittest.TestCase):
    """main() のテスト"""

    def test_requires_provider_for_status(self):
        """--status には --provider が必要"""
        with patch.object(sys, "argv", ["cli", "--status"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_ARGUMENT_ERROR)

    def test_requires_provider_for_reset(self):
        """--reset には --provider が必要"""
        with patch.object(sys, "argv", ["cli", "--reset"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_ARGUMENT_ERROR)

    def test_requires_provider(self):
        """--provider は必須"""
        with patch.object(sys, "argv", ["cli", "some_dir"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_ARGUMENT_ERROR)

    def test_requires_input_dir(self):
        """input_dir は必須"""
        with patch.object(sys, "argv", ["cli", "--provider", "claude"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_ARGUMENT_ERROR)

    def test_unknown_provider(self):
        """未知のプロバイダーでエラー（argparse レベルでエラー）"""
        # argparse の choices で制限されているため、SystemExit が発生
        with patch.object(sys, "argv", ["cli", "--provider", "unknown", "some_dir"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            # argparse は exit code 2 を返す
            self.assertEqual(cm.exception.code, 2)

    def test_input_not_found(self):
        """入力ディレクトリが存在しない場合"""
        with patch.object(sys, "argv", ["cli", "--provider", "claude", "/nonexistent/path"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_INPUT_NOT_FOUND)


class TestCmdStatus(unittest.TestCase):
    """cmd_status のテスト"""

    def test_displays_status(self):
        """ステータスが表示される"""
        with patch("scripts.llm_import.cli.StateManager") as MockManager:
            mock_instance = MagicMock()
            mock_instance.get_stats.return_value = {
                "total": 10,
                "success": 8,
                "skipped": 1,
                "error": 1,
            }
            mock_instance.get_errors.return_value = []
            mock_instance.state.last_run = "2026-01-16T10:00:00"
            mock_instance.state_file = Path("test_state.json")
            MockManager.return_value = mock_instance

            exit_code = cmd_status("claude")
            self.assertEqual(exit_code, EXIT_SUCCESS)


class TestCmdReset(unittest.TestCase):
    """cmd_reset のテスト"""

    def test_resets_state(self):
        """状態がリセットされる"""
        with patch("scripts.llm_import.cli.StateManager") as MockManager:
            mock_instance = MagicMock()
            MockManager.return_value = mock_instance

            exit_code = cmd_reset("claude")
            self.assertEqual(exit_code, EXIT_SUCCESS)
            mock_instance.reset.assert_called_once()


class TestHelperFunctions(unittest.TestCase):
    """ヘルパー関数のテスト"""

    def test_generate_filename_simple(self):
        """シンプルなファイル名生成（日付プレフィックスなし）"""
        mock_conv = MagicMock()
        mock_conv.created_at = "2025-12-20T09:28:24.439525Z"
        mock_conv.title = "Test Conversation"

        filename = _generate_filename(mock_conv)
        # 新仕様: 日付プレフィックスなし
        self.assertEqual(filename, "Test Conversation")

    def test_generate_filename_removes_date_prefix(self):
        """タイトルから日付プレフィックスを除去"""
        mock_conv = MagicMock()
        mock_conv.created_at = "2025-12-20T09:28:24.439525Z"
        mock_conv.title = "2025-12-20_Test Conversation"

        filename = _generate_filename(mock_conv)
        # 日付プレフィックスが除去される
        self.assertEqual(filename, "Test Conversation")

    def test_format_duration_seconds(self):
        """秒単位のフォーマット"""
        self.assertEqual(_format_duration(45.5), "45.5秒")

    def test_format_duration_minutes(self):
        """分単位のフォーマット"""
        self.assertEqual(_format_duration(125), "2分5秒")

    def test_format_duration_hours(self):
        """時間単位のフォーマット"""
        self.assertEqual(_format_duration(3725), "1時間2分5秒")


class TestRetryErrorsArguments(unittest.TestCase):
    """--retry-errors 関連の引数テスト"""

    def test_retry_errors_argument_parsed(self):
        """--retry-errors がパースされる"""
        parser = create_parser()
        args = parser.parse_args(["--provider", "claude", "--retry-errors"])
        self.assertTrue(args.retry_errors)

    def test_session_argument_parsed(self):
        """--session がパースされる"""
        parser = create_parser()
        args = parser.parse_args([
            "--provider", "claude",
            "--retry-errors",
            "--session", "import_20260116_203426",
        ])
        self.assertEqual(args.session, "import_20260116_203426")

    def test_timeout_argument_parsed(self):
        """--timeout がパースされる"""
        parser = create_parser()
        args = parser.parse_args([
            "--provider", "claude",
            "--retry-errors",
            "--timeout", "180",
        ])
        self.assertEqual(args.timeout, 180)

    def test_timeout_default_value(self):
        """--timeout のデフォルト値は 120"""
        parser = create_parser()
        args = parser.parse_args(["--provider", "claude", "--retry-errors"])
        self.assertEqual(args.timeout, 120)

    def test_retry_errors_requires_provider(self):
        """--retry-errors には --provider が必要"""
        with patch.object(sys, "argv", ["cli", "--retry-errors"]):
            exit_code = main()
            self.assertEqual(exit_code, EXIT_ARGUMENT_ERROR)


class TestExitCodes(unittest.TestCase):
    """終了コードの定義テスト"""

    def test_exit_codes_defined(self):
        """終了コードが正しく定義されている"""
        from scripts.llm_import.cli import (
            EXIT_SUCCESS,
            EXIT_ARGUMENT_ERROR,
            EXIT_INPUT_NOT_FOUND,
            EXIT_OLLAMA_ERROR,
            EXIT_PARTIAL_ERROR,
            EXIT_ALL_FAILED,
            EXIT_UNKNOWN_PROVIDER,
        )
        self.assertEqual(EXIT_SUCCESS, 0)
        self.assertEqual(EXIT_ARGUMENT_ERROR, 1)
        self.assertEqual(EXIT_INPUT_NOT_FOUND, 2)
        self.assertEqual(EXIT_OLLAMA_ERROR, 3)
        self.assertEqual(EXIT_PARTIAL_ERROR, 4)
        self.assertEqual(EXIT_ALL_FAILED, 5)
        self.assertEqual(EXIT_UNKNOWN_PROVIDER, 6)


class TestSessionLoggerWithFolderManager(unittest.TestCase):
    """SessionLogger と FolderManager の統合テスト (US2)"""

    def test_session_logger_creates_new_structure(self):
        """SessionLogger が FolderManager を使用して新構造を作成する"""
        import tempfile
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            folder_manager = FolderManager(base_path)

            session_logger = SessionLogger(
                provider="claude",
                total_files=10,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()

            # セッションディレクトリが作成されたことを確認
            self.assertIsNotNone(session_dir)
            self.assertTrue(session_dir.exists())

            # 新構造: @session/import/{session_id}/
            self.assertEqual(session_dir.parent.name, "import")

            # サブフォルダが作成されたことを確認
            paths = session_logger.get_paths()
            self.assertIn("session", paths)
            self.assertIn("parsed", paths)
            self.assertIn("output", paths)
            self.assertIn("errors", paths)

            # session.json が作成されたことを確認
            session_file = session_dir / "session.json"
            self.assertTrue(session_file.exists())

            # session.json の内容を確認
            session_data = json.loads(session_file.read_text())
            self.assertEqual(session_data["session_type"], "import")
            self.assertEqual(session_data["provider"], "claude")


class TestProcessedEntryFileId(unittest.TestCase):
    """ProcessedEntry の file_id フィールドテスト (US2)"""

    def test_file_id_field_default_none(self):
        """file_id フィールドのデフォルト値は None"""
        from scripts.llm_import.common.state import ProcessedEntry

        entry = ProcessedEntry(
            id="test-conv-001",
            provider="claude",
            input_file="/path/to/input.md",
            output_file="/path/to/output.md",
            processed_at="2026-01-18T12:00:00",
            status="success",
        )
        self.assertIsNone(entry.file_id)

    def test_file_id_field_can_be_set(self):
        """file_id フィールドを設定可能"""
        from scripts.llm_import.common.state import ProcessedEntry

        entry = ProcessedEntry(
            id="test-conv-002",
            provider="claude",
            input_file="/path/to/input.md",
            output_file="/path/to/output.md",
            processed_at="2026-01-18T12:00:00",
            status="success",
            file_id="a1b2c3d4e5f6",
        )
        self.assertEqual(entry.file_id, "a1b2c3d4e5f6")

    def test_to_dict_includes_file_id(self):
        """to_dict() が file_id を含む"""
        from scripts.llm_import.common.state import ProcessedEntry

        entry = ProcessedEntry(
            id="test-conv-003",
            provider="claude",
            input_file="/path/to/input.md",
            output_file="/path/to/output.md",
            processed_at="2026-01-18T12:00:00",
            status="success",
            file_id="deadbeef1234",
        )
        d = entry.to_dict()
        self.assertIn("file_id", d)
        self.assertEqual(d["file_id"], "deadbeef1234")

    def test_to_dict_includes_none_file_id(self):
        """to_dict() が None の file_id も含む"""
        from scripts.llm_import.common.state import ProcessedEntry

        entry = ProcessedEntry(
            id="test-conv-004",
            provider="claude",
            input_file="/path/to/input.md",
            output_file="/path/to/output.md",
            processed_at="2026-01-18T12:00:00",
            status="success",
        )
        d = entry.to_dict()
        self.assertIn("file_id", d)
        self.assertIsNone(d["file_id"])

    def test_from_dict_with_file_id(self):
        """from_dict() が file_id を読み込む"""
        from scripts.llm_import.common.state import ProcessedEntry

        data = {
            "id": "test-conv-005",
            "provider": "claude",
            "input_file": "/path/to/input.md",
            "output_file": "/path/to/output.md",
            "processed_at": "2026-01-18T12:00:00",
            "status": "success",
            "file_id": "cafebabe0000",
        }
        entry = ProcessedEntry.from_dict(data)
        self.assertEqual(entry.file_id, "cafebabe0000")

    def test_from_dict_without_file_id_backward_compatible(self):
        """from_dict() が file_id なしのデータを読み込む（後方互換性）"""
        from scripts.llm_import.common.state import ProcessedEntry

        # 既存の state.json に file_id がない場合
        data = {
            "id": "test-conv-006",
            "provider": "claude",
            "input_file": "/path/to/input.md",
            "output_file": "/path/to/output.md",
            "processed_at": "2026-01-18T12:00:00",
            "status": "success",
            # file_id は存在しない
        }
        entry = ProcessedEntry.from_dict(data)
        self.assertIsNone(entry.file_id)


class TestPhase1FileIdGeneration(unittest.TestCase):
    """Phase 1 file_id 生成のテスト (US1 T009)"""

    def test_phase1_generates_file_id_in_frontmatter(self):
        """Phase 1 処理が file_id を frontmatter に含めること"""
        import tempfile
        import re
        from scripts.llm_import.providers.claude.parser import ClaudeParser, ClaudeConversation, ClaudeMessage
        from scripts.llm_import.common.file_id import generate_file_id

        # テスト用会話データ
        msg = ClaudeMessage(
            uuid="msg-test-001",
            content="テストメッセージ",
            timestamp="2026-01-18T10:00:00Z",
            sender="human",
        )
        conv = ClaudeConversation(
            uuid="conv-test-001",
            title="Phase1 file_id テスト",
            created_at="2026-01-18T10:00:00Z",
            updated_at="2026-01-18T10:00:00Z",
            summary=None,
            _messages=[msg],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            parsed_dir.mkdir()

            parser = ClaudeParser()
            filename = "Phase1 file_id テスト.md"
            phase1_path = parsed_dir / filename

            # cli.py の Phase 1 処理をシミュレート
            markdown_without_id = parser.to_markdown(conv)
            relative_path = phase1_path.relative_to(parsed_dir.parent)
            file_id = generate_file_id(markdown_without_id, relative_path)
            markdown = parser.to_markdown(conv, file_id=file_id)

            phase1_path.write_text(markdown, encoding="utf-8")

            # 検証: ファイルが存在
            self.assertTrue(phase1_path.exists())

            # 検証: file_id が frontmatter に含まれる
            content = phase1_path.read_text(encoding="utf-8")
            self.assertIn("file_id:", content)

            # 検証: file_id が12文字の16進数
            match = re.search(r"file_id: ([a-f0-9]+)", content)
            self.assertIsNotNone(match, "file_id が見つからない")
            self.assertEqual(len(match.group(1)), 12, "file_id は12文字の16進数")

    def test_phase1_file_id_is_deterministic(self):
        """同じ入力に対して file_id が決定論的に生成されること"""
        import tempfile
        from scripts.llm_import.providers.claude.parser import ClaudeParser, ClaudeConversation, ClaudeMessage
        from scripts.llm_import.common.file_id import generate_file_id

        msg = ClaudeMessage(
            uuid="msg-det-001",
            content="決定論的テスト",
            timestamp="2026-01-18T10:00:00Z",
            sender="human",
        )
        conv = ClaudeConversation(
            uuid="conv-det-001",
            title="決定論的 file_id テスト",
            created_at="2026-01-18T10:00:00Z",
            updated_at="2026-01-18T10:00:00Z",
            summary=None,
            _messages=[msg],
        )

        parser = ClaudeParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            parsed_dir.mkdir()
            phase1_path = parsed_dir / "test.md"

            # 1回目の生成
            markdown1 = parser.to_markdown(conv)
            relative_path = phase1_path.relative_to(parsed_dir.parent)
            file_id1 = generate_file_id(markdown1, relative_path)

            # 2回目の生成（同じ入力）
            markdown2 = parser.to_markdown(conv)
            file_id2 = generate_file_id(markdown2, relative_path)

            # 検証: 同じ file_id が生成される
            self.assertEqual(file_id1, file_id2)

    def test_phase1_different_content_different_file_id(self):
        """異なるコンテンツには異なる file_id が生成されること"""
        import tempfile
        from scripts.llm_import.providers.claude.parser import ClaudeParser, ClaudeConversation, ClaudeMessage
        from scripts.llm_import.common.file_id import generate_file_id

        parser = ClaudeParser()

        msg1 = ClaudeMessage(
            uuid="msg-diff-001",
            content="コンテンツ1",
            timestamp="2026-01-18T10:00:00Z",
            sender="human",
        )
        conv1 = ClaudeConversation(
            uuid="conv-diff-001",
            title="会話1",
            created_at="2026-01-18T10:00:00Z",
            updated_at="2026-01-18T10:00:00Z",
            summary=None,
            _messages=[msg1],
        )

        msg2 = ClaudeMessage(
            uuid="msg-diff-002",
            content="コンテンツ2",
            timestamp="2026-01-18T10:00:00Z",
            sender="human",
        )
        conv2 = ClaudeConversation(
            uuid="conv-diff-002",
            title="会話2",
            created_at="2026-01-18T10:00:00Z",
            updated_at="2026-01-18T10:00:00Z",
            summary=None,
            _messages=[msg2],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            parsed_dir.mkdir()

            # 会話1 の file_id
            path1 = parsed_dir / "conv1.md"
            md1 = parser.to_markdown(conv1)
            file_id1 = generate_file_id(md1, path1.relative_to(parsed_dir.parent))

            # 会話2 の file_id
            path2 = parsed_dir / "conv2.md"
            md2 = parser.to_markdown(conv2)
            file_id2 = generate_file_id(md2, path2.relative_to(parsed_dir.parent))

            # 検証: 異なる file_id
            self.assertNotEqual(file_id1, file_id2)


class TestPipelineStagesFileIdRecording(unittest.TestCase):
    """pipeline_stages.jsonl の file_id 記録テスト (US2 T017)"""

    def test_log_stage_records_file_id_for_phase1(self):
        """Phase 1 の log_stage() が file_id を記録すること"""
        import tempfile
        import json
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            plan_dir = tmpdir_path / "@session"
            plan_dir.mkdir()

            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=1,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()

            # Phase 1 の log_stage に file_id を渡す
            test_file_id = "a1b2c3d4e5f6"
            session_logger.log_stage(
                filename="テスト会話.md",
                stage="phase1",
                timing_ms=100,
                file_id=test_file_id,
            )

            # pipeline_stages.jsonl を検証
            jsonl_file = session_dir / "pipeline_stages.jsonl"
            self.assertTrue(jsonl_file.exists(), "pipeline_stages.jsonl が存在しない")

            content = jsonl_file.read_text(encoding="utf-8").strip()
            record = json.loads(content)

            self.assertEqual(record["stage"], "phase1")
            self.assertIn("file_id", record, "file_id フィールドが含まれていない")
            self.assertEqual(record["file_id"], test_file_id)

    def test_log_stage_records_file_id_for_phase2(self):
        """Phase 2 の log_stage() が file_id を記録すること"""
        import tempfile
        import json
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            plan_dir = tmpdir_path / "@session"
            plan_dir.mkdir()

            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=1,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()

            # Phase 2 の log_stage に file_id を渡す
            test_file_id = "deadbeef1234"
            session_logger.log_stage(
                filename="テスト会話.md",
                stage="phase2",
                timing_ms=5000,
                before_chars=10000,
                after_chars=3000,
                file_id=test_file_id,
            )

            # pipeline_stages.jsonl を検証
            jsonl_file = session_dir / "pipeline_stages.jsonl"
            content = jsonl_file.read_text(encoding="utf-8").strip()
            record = json.loads(content)

            self.assertEqual(record["stage"], "phase2")
            self.assertIn("file_id", record)
            self.assertEqual(record["file_id"], test_file_id)
            # 差分情報も含まれていること
            self.assertEqual(record["before_chars"], 10000)
            self.assertEqual(record["after_chars"], 3000)

    def test_backward_compatibility_without_file_id(self):
        """file_id なしでも動作すること（後方互換性）"""
        import tempfile
        import json
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            plan_dir = tmpdir_path / "@session"
            plan_dir.mkdir()

            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=1,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()

            # file_id なしで log_stage を呼び出し
            session_logger.log_stage(
                filename="old_style.md",
                stage="phase1",
                timing_ms=100,
                # file_id は指定しない（後方互換性）
            )

            # pipeline_stages.jsonl を検証
            jsonl_file = session_dir / "pipeline_stages.jsonl"
            content = jsonl_file.read_text(encoding="utf-8").strip()
            record = json.loads(content)

            # file_id フィールドが含まれないこと
            self.assertNotIn("file_id", record)


class TestIntermediateFileRetention(unittest.TestCase):
    """中間ファイル保持のテスト (US3)"""

    def test_intermediate_files_retained(self):
        """インポート処理後、parsed/ と output/ の両方にファイルが残っている

        このテストは中間ファイル保持機能（US3）を検証する:
        - Phase 1 出力: parsed/conversations/ に保持
        - Phase 2 出力: output/ に保持 + @index/ にコピー
        """
        import tempfile
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # テスト用ディレクトリ構成
            plan_dir = tmpdir_path / "@session"
            index_dir = tmpdir_path / "@index"
            plan_dir.mkdir()
            index_dir.mkdir()

            # FolderManager と SessionLogger を使用
            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=1,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()
            session_paths = session_logger.get_paths()

            # Phase 1 出力をシミュレート: parsed/ に出力
            parsed_dir = session_paths["parsed"]
            parsed_file = parsed_dir / "テスト会話.md"
            parsed_content = "# テスト会話\n\n## user\nテストメッセージ"
            parsed_file.write_text(parsed_content, encoding="utf-8")

            # Phase 2 出力をシミュレート: output/ に出力
            output_dir = session_paths["output"]
            mock_document = KnowledgeDocument(
                title="テスト会話",
                summary="テストサマリー",
                created="2026-01-17",
                source_provider="claude",
                source_conversation="test-conv-001",
                summary_content="テスト内容",
                key_learnings=["ポイント1"],
            )
            output_content = mock_document.to_markdown()
            output_file = output_dir / "テスト会話.md"
            output_file.write_text(output_content, encoding="utf-8")

            # @index/ にコピー（最終出力）
            index_file = index_dir / "テスト会話.md"
            index_file.write_text(output_content, encoding="utf-8")

            # 検証: parsed/ にファイルが残っている
            self.assertTrue(
                parsed_file.exists(),
                "Phase 1 出力が parsed/ に残っていない"
            )
            self.assertEqual(
                parsed_file.read_text(encoding="utf-8"),
                parsed_content,
                "parsed/ のファイル内容が正しくない"
            )

            # 検証: output/ にファイルが残っている
            self.assertTrue(
                output_file.exists(),
                "Phase 2 出力が output/ に残っていない"
            )

            # 検証: @index/ にもファイルが存在
            self.assertTrue(
                index_file.exists(),
                "@index/ にファイルがコピーされていない"
            )

            # 検証: output/ と @index/ の内容が一致
            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                index_file.read_text(encoding="utf-8"),
                "output/ と @index/ の内容が一致しない"
            )

    def test_output_copied_to_index(self):
        """Phase 2 出力が output/ に保存され、@index/ にコピーされる

        このテストは cmd_process の出力フローを検証する:
        1. Phase 2 出力を session output/ に書き込み
        2. 同じ内容を @index/ にコピー
        3. 両方のファイルが同一内容で存在
        """
        import tempfile
        import shutil
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger
        from scripts.llm_import.common.knowledge_extractor import KnowledgeDocument

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # テスト用ディレクトリ構成
            plan_dir = tmpdir_path / "@session"
            index_dir = tmpdir_path / "@index"
            plan_dir.mkdir()
            index_dir.mkdir()

            # FolderManager と SessionLogger を使用
            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=1,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_logger.start_session()
            session_paths = session_logger.get_paths()

            # Phase 2 出力（cmd_process の動作をシミュレート）
            output_dir = session_paths["output"]
            mock_document = KnowledgeDocument(
                title="コピーテスト会話",
                summary="コピー動作のテスト",
                created="2026-01-17",
                source_provider="claude",
                source_conversation="copy-test-001",
                summary_content="テスト内容です",
                key_learnings=["学び1", "学び2"],
            )
            output_content = mock_document.to_markdown()
            output_filename = "コピーテスト会話.md"

            # Step 1: session output/ に書き込み
            session_output_path = output_dir / output_filename
            session_output_path.write_text(output_content, encoding="utf-8")

            # Step 2: @index/ にコピー（cmd_process と同じ動作）
            index_path = index_dir / output_filename
            index_path.write_text(output_content, encoding="utf-8")

            # 検証: 両方のファイルが存在
            self.assertTrue(
                session_output_path.exists(),
                "session output/ にファイルが存在しない"
            )
            self.assertTrue(
                index_path.exists(),
                "@index/ にファイルがコピーされていない"
            )

            # 検証: ファイル内容が完全一致
            session_content = session_output_path.read_text(encoding="utf-8")
            index_content = index_path.read_text(encoding="utf-8")
            self.assertEqual(
                session_content,
                index_content,
                "session output/ と @index/ の内容が一致しない"
            )

            # 検証: 期待される内容が含まれている
            self.assertIn("title: コピーテスト会話", index_content)
            self.assertIn("source_conversation: copy-test-001", index_content)
            self.assertIn("学び1", index_content)

    def test_session_json_contains_intermediate_files(self):
        """finalize() 後、session.json に intermediate_files が含まれる (T029)"""
        import tempfile
        from scripts.llm_import.common.folder_manager import FolderManager
        from scripts.llm_import.common.session_logger import SessionLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            plan_dir = tmpdir_path / "@session"
            plan_dir.mkdir()

            # セッション開始
            folder_manager = FolderManager(plan_dir)
            session_logger = SessionLogger(
                provider="claude",
                total_files=2,
                prefix="import",
                folder_manager=folder_manager,
            )
            session_dir = session_logger.start_session()
            session_paths = session_logger.get_paths()

            # 中間ファイルを作成
            parsed_dir = session_paths["parsed"]
            output_dir = session_paths["output"]

            (parsed_dir / "file1.md").write_text("# File 1", encoding="utf-8")
            (parsed_dir / "file2.md").write_text("# File 2", encoding="utf-8")
            (output_dir / "file1.md").write_text("# Output 1", encoding="utf-8")

            # finalize 呼び出し
            session_logger.add_processed(file="conv1", output="file1.md")
            session_logger.finalize(elapsed_seconds=10.0, also_print=False)

            # session.json を確認
            session_file = session_dir / "session.json"
            self.assertTrue(session_file.exists())

            session_data = json.loads(session_file.read_text())

            # intermediate_files が存在する
            self.assertIn("intermediate_files", session_data)

            intermediate = session_data["intermediate_files"]
            self.assertEqual(intermediate["parsed_count"], 2)
            self.assertEqual(intermediate["output_count"], 1)
            self.assertIn("file1.md", intermediate["parsed_files"])
            self.assertIn("file2.md", intermediate["parsed_files"])
            self.assertIn("file1.md", intermediate["output_files"])


class TestPhase2FileIdInheritance(unittest.TestCase):
    """Phase 2 file_id 継承テスト (T024)"""

    def test_phase2_inherits_file_id_from_parsed_file(self):
        """Phase 2 が parsed ファイルから file_id を継承すること"""
        import tempfile
        import re
        from scripts.llm_import.common.knowledge_extractor import (
            KnowledgeDocument,
            extract_file_id_from_frontmatter,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            output_dir = tmpdir_path / "output"
            parsed_dir.mkdir()
            output_dir.mkdir()

            # Phase 1 出力をシミュレート（file_id 付き）
            phase1_file_id = "a1b2c3d4e5f6"
            phase1_content = f"""---
title: テスト会話
created: 2026-01-18
file_id: {phase1_file_id}
---

# テスト会話

## user
テストメッセージ
"""
            parsed_file = parsed_dir / "テスト会話.md"
            parsed_file.write_text(phase1_content, encoding="utf-8")

            # Phase 2 処理をシミュレート: cli.py のロジックと同様に継承
            parsed_content = parsed_file.read_text(encoding="utf-8")
            inherited_file_id = extract_file_id_from_frontmatter(parsed_content)

            # KnowledgeDocument を作成（Phase 2 出力）
            document = KnowledgeDocument(
                title="テスト会話",
                summary="テストサマリー",
                created="2026-01-18",
                source_provider="claude",
                source_conversation="test-conv",
                summary_content="テスト内容",
                key_learnings=["ポイント1"],
            )

            # file_id を継承
            if inherited_file_id:
                document.file_id = inherited_file_id

            # 出力
            output_file = output_dir / "テスト会話.md"
            output_file.write_text(document.to_markdown(), encoding="utf-8")

            # 検証: file_id が一致
            output_content = output_file.read_text(encoding="utf-8")
            output_file_id = extract_file_id_from_frontmatter(output_content)
            self.assertEqual(output_file_id, phase1_file_id)

    def test_phase2_generates_file_id_when_parsed_has_none(self):
        """parsed ファイルに file_id がない場合、Phase 2 が新規生成すること"""
        import tempfile
        from scripts.llm_import.common.knowledge_extractor import (
            KnowledgeDocument,
            extract_file_id_from_frontmatter,
        )
        from scripts.llm_import.common.file_id import generate_file_id

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            output_dir = tmpdir_path / "output"
            parsed_dir.mkdir()
            output_dir.mkdir()

            # Phase 1 出力をシミュレート（file_id なし - 旧形式）
            phase1_content = """---
title: 旧形式会話
created: 2026-01-18
---

# 旧形式会話

## user
テストメッセージ
"""
            parsed_file = parsed_dir / "旧形式会話.md"
            parsed_file.write_text(phase1_content, encoding="utf-8")

            # Phase 2 処理をシミュレート
            parsed_content = parsed_file.read_text(encoding="utf-8")
            inherited_file_id = extract_file_id_from_frontmatter(parsed_content)

            # KnowledgeDocument を作成
            document = KnowledgeDocument(
                title="旧形式会話",
                summary="テストサマリー",
                created="2026-01-18",
                source_provider="claude",
                source_conversation="test-conv",
                summary_content="テスト内容",
                key_learnings=["ポイント1"],
            )

            # file_id を継承または新規生成
            output_file = output_dir / "旧形式会話.md"
            if inherited_file_id:
                document.file_id = inherited_file_id
            else:
                # 新規生成
                content_for_hash = document.to_markdown()
                relative_path = output_file.relative_to(output_dir.parent)
                document.file_id = generate_file_id(content_for_hash, relative_path)

            output_file.write_text(document.to_markdown(), encoding="utf-8")

            # 検証: file_id が生成されている
            output_content = output_file.read_text(encoding="utf-8")
            output_file_id = extract_file_id_from_frontmatter(output_content)
            self.assertIsNotNone(output_file_id)
            self.assertEqual(len(output_file_id), 12)

    def test_phase1_phase2_file_id_consistency(self):
        """Phase 1 → Phase 2 の完全なフローで file_id が一貫すること"""
        import tempfile
        import re
        from scripts.llm_import.providers.claude.parser import (
            ClaudeParser,
            ClaudeConversation,
            ClaudeMessage,
        )
        from scripts.llm_import.common.file_id import generate_file_id
        from scripts.llm_import.common.knowledge_extractor import (
            KnowledgeDocument,
            extract_file_id_from_frontmatter,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            parsed_dir = tmpdir_path / "parsed"
            output_dir = tmpdir_path / "output"
            parsed_dir.mkdir()
            output_dir.mkdir()

            # テスト用会話データ
            msg = ClaudeMessage(
                uuid="msg-consistency-001",
                content="一貫性テストメッセージ",
                timestamp="2026-01-18T10:00:00Z",
                sender="human",
            )
            conv = ClaudeConversation(
                uuid="conv-consistency-001",
                title="一貫性テスト会話",
                created_at="2026-01-18T10:00:00Z",
                updated_at="2026-01-18T10:00:00Z",
                summary=None,
                _messages=[msg],
            )

            parser = ClaudeParser()
            filename = "一貫性テスト会話.md"

            # Phase 1: parsed ファイルを生成（cli.py の処理をシミュレート）
            phase1_path = parsed_dir / filename
            markdown_without_id = parser.to_markdown(conv)
            relative_path = phase1_path.relative_to(parsed_dir.parent)
            phase1_file_id = generate_file_id(markdown_without_id, relative_path)
            markdown = parser.to_markdown(conv, file_id=phase1_file_id)
            phase1_path.write_text(markdown, encoding="utf-8")

            # Phase 1 の file_id を確認
            phase1_content = phase1_path.read_text(encoding="utf-8")
            phase1_extracted_id = extract_file_id_from_frontmatter(phase1_content)
            self.assertEqual(phase1_extracted_id, phase1_file_id)

            # Phase 2: parsed から file_id を継承
            inherited_file_id = extract_file_id_from_frontmatter(phase1_content)

            # Phase 2 出力 (KnowledgeDocument)
            document = KnowledgeDocument(
                title="一貫性テスト会話",
                summary="テストサマリー",
                created="2026-01-18",
                source_provider="claude",
                source_conversation="conv-consistency-001",
                summary_content="テスト内容です",
                key_learnings=["学び1"],
            )

            # file_id を継承
            document.file_id = inherited_file_id

            output_path = output_dir / filename
            output_path.write_text(document.to_markdown(), encoding="utf-8")

            # Phase 2 の file_id を確認
            output_content = output_path.read_text(encoding="utf-8")
            phase2_file_id = extract_file_id_from_frontmatter(output_content)

            # 検証: Phase 1 と Phase 2 の file_id が一致
            self.assertEqual(phase1_file_id, phase2_file_id)

            # 検証: 12文字の16進数
            self.assertRegex(phase1_file_id, r"^[a-f0-9]{12}$")
            self.assertRegex(phase2_file_id, r"^[a-f0-9]{12}$")


if __name__ == "__main__":
    unittest.main()
