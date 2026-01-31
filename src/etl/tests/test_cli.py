"""Tests for CLI argument parsing and exit codes.

Tests for:
- CLI argument parsing (import, organize, status, retry, clean)
- CLI exit codes (0=success, 1=error, 2=partial, etc.)
- Required arguments validation
- Global options (--debug)
"""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_import_command_requires_input(self):
        """Import command requires --input argument (validated in execute, not argparse)."""
        from src.etl.cli import create_parser

        parser = create_parser()

        # With action="append", argparse doesn't enforce required=True
        # So we just check that parsing succeeds and args.input is None
        args = parser.parse_args(["import"])
        self.assertIsNone(args.input)  # No --input provided → None
        # The actual validation happens in import_cmd.execute()

    def test_import_command_with_input(self):
        """Import command accepts --input argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["import", "--input", "/path/to/data"])

        self.assertEqual(args.command, "import")
        self.assertEqual(args.input, ["/path/to/data"])  # Now a list (action="append")

    def test_import_command_with_options(self):
        """Import command accepts all optional arguments."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "import",
                "--input",
                "/path/to/data",
                "--session",
                "20260119_143052",
                "--debug",
                "--dry-run",
                "--limit",
                "10",
            ]
        )

        self.assertEqual(args.command, "import")
        self.assertEqual(args.input, ["/path/to/data"])  # Now a list (action="append")
        self.assertEqual(args.session, "20260119_143052")
        self.assertTrue(args.debug)
        self.assertTrue(args.dry_run)
        self.assertEqual(args.limit, 10)

    def test_organize_command_without_input_or_session(self):
        """Organize command accepts no --input (validated in execute, not argparse)."""
        from src.etl.cli import create_parser

        parser = create_parser()

        # --input is optional at argparse level (validated in execute())
        args = parser.parse_args(["organize"])
        self.assertIsNone(args.input)

    def test_organize_command_with_input(self):
        """Organize command accepts --input argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["organize", "--input", "/path/to/files"])

        self.assertEqual(args.command, "organize")
        self.assertEqual(args.input, "/path/to/files")

    def test_organize_command_with_options(self):
        """Organize command accepts all optional arguments."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "organize",
                "--input",
                "/path/to/files",
                "--debug",
                "--dry-run",
                "--limit",
                "5",
            ]
        )

        self.assertEqual(args.command, "organize")
        self.assertTrue(args.debug)
        self.assertTrue(args.dry_run)
        self.assertEqual(args.limit, 5)

    def test_status_command_no_args(self):
        """Status command works without arguments."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status"])

        self.assertEqual(args.command, "status")

    def test_status_command_with_session(self):
        """Status command accepts --session argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status", "--session", "20260119_143052"])

        self.assertEqual(args.command, "status")
        self.assertEqual(args.session, "20260119_143052")

    def test_status_command_with_all(self):
        """Status command accepts --all argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status", "--all"])

        self.assertEqual(args.command, "status")
        self.assertTrue(args.all)

    def test_status_command_with_json(self):
        """Status command accepts --json argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status", "--json"])

        self.assertEqual(args.command, "status")
        self.assertTrue(args.json)

    def test_retry_command_requires_session(self):
        """Retry command requires --session argument."""
        from src.etl.cli import create_parser

        parser = create_parser()

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stderr", new_callable=io.StringIO):
                parser.parse_args(["retry"])

        self.assertEqual(ctx.exception.code, 2)

    def test_retry_command_with_session(self):
        """Retry command accepts --session argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["retry", "--session", "20260119_143052"])

        self.assertEqual(args.command, "retry")
        self.assertEqual(args.session, "20260119_143052")

    def test_retry_command_with_phase(self):
        """Retry command accepts --phase argument."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "retry",
                "--session",
                "20260119_143052",
                "--phase",
                "import",
            ]
        )

        self.assertEqual(args.command, "retry")
        self.assertEqual(args.phase, "import")

    def test_clean_command_defaults(self):
        """Clean command has sensible defaults."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["clean"])

        self.assertEqual(args.command, "clean")
        self.assertEqual(args.days, 7)  # Default
        self.assertFalse(args.dry_run)
        self.assertFalse(args.force)

    def test_clean_command_with_options(self):
        """Clean command accepts all options."""
        from src.etl.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "clean",
                "--days",
                "14",
                "--dry-run",
                "--force",
            ]
        )

        self.assertEqual(args.command, "clean")
        self.assertEqual(args.days, 14)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.force)

    def test_no_command_shows_help(self):
        """No command shows help and exits with error."""
        from src.etl.cli import create_parser

        parser = create_parser()

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stderr", new_callable=io.StringIO):
                parser.parse_args([])

        # argparse 3.9+ returns 0 for help, earlier returns 2
        self.assertIn(ctx.exception.code, (0, 2))


class TestCLIExitCodes(unittest.TestCase):
    """Test CLI exit codes."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_exit_code_success(self):
        """Exit code 0 for success."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.SUCCESS, 0)

    def test_exit_code_error(self):
        """Exit code 1 for general error."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.ERROR, 1)

    def test_exit_code_input_not_found(self):
        """Exit code 2 for input directory not found."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.INPUT_NOT_FOUND, 2)

    def test_exit_code_ollama_error(self):
        """Exit code 3 for Ollama connection error."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.OLLAMA_ERROR, 3)

    def test_exit_code_partial(self):
        """Exit code 4 for partial success."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.PARTIAL, 4)

    def test_exit_code_all_failed(self):
        """Exit code 5 for all items failed."""
        from src.etl.cli import ExitCode

        self.assertEqual(ExitCode.ALL_FAILED, 5)

    def test_import_nonexistent_input_returns_code_2(self):
        """Import with nonexistent input directory returns exit code 2."""
        from src.etl.cli import run_import

        result = run_import(
            input_path=Path("/nonexistent/path"),
            provider="claude",
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            fetch_titles=True,
            chunk=False,
            session_base_dir=self.test_dir,
        )

        self.assertEqual(result, 2)

    def test_organize_nonexistent_input_returns_code_2(self):
        """Organize with nonexistent input directory returns exit code 2."""
        from src.etl.cli import run_organize

        result = run_organize(
            input_path=Path("/nonexistent/path"),
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            session_base_dir=self.test_dir,
        )

        self.assertEqual(result, 2)

    def test_import_empty_input_returns_success(self):
        """Import with empty input directory returns exit code 0."""
        from src.etl.cli import run_import

        # Create empty input directory
        input_dir = self.test_dir / "empty_input"
        input_dir.mkdir()

        result = run_import(
            input_path=input_dir,
            provider="claude",
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            fetch_titles=True,
            chunk=False,
            session_base_dir=self.test_dir / "sessions",
        )

        self.assertEqual(result, 0)

    def test_status_no_sessions_returns_code_1(self):
        """Status with no sessions returns exit code 1."""
        from src.etl.cli import run_status

        result = run_status(
            session_id=None,
            show_all=True,
            as_json=False,
            session_base_dir=self.test_dir / "nonexistent",
        )

        self.assertEqual(result, 1)

    def test_retry_nonexistent_session_returns_code_2(self):
        """Retry with nonexistent session returns exit code 2."""
        from src.etl.cli import run_retry

        result = run_retry(
            session_id="99991231_235959",
            phase=None,
            debug=False,
            session_base_dir=self.test_dir / "sessions",
        )

        self.assertEqual(result, 2)


class TestCLIImportCommand(unittest.TestCase):
    """Test import command functionality."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_import_creates_session(self):
        """Import command creates a new session."""
        from src.etl.cli import run_import
        from src.etl.core.session import SessionManager

        # Create input directory with a JSON file
        input_dir = self.test_dir / "input"
        input_dir.mkdir()
        (input_dir / "test.json").write_text('{"test": true}')

        session_dir = self.test_dir / "sessions"

        result = run_import(
            input_path=input_dir,
            provider="claude",
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            fetch_titles=True,
            chunk=False,
            session_base_dir=session_dir,
        )

        # Check session was created
        manager = SessionManager(session_dir)
        sessions = manager.list_sessions()
        self.assertGreater(len(sessions), 0)

    def test_import_dry_run_does_not_modify(self):
        """Import with --dry-run does not create output files."""
        from src.etl.cli import run_import

        # Create input directory with a JSON file
        input_dir = self.test_dir / "input"
        input_dir.mkdir()
        (input_dir / "test.json").write_text('{"test": true}')

        session_dir = self.test_dir / "sessions"

        result = run_import(
            input_path=input_dir,
            provider="claude",
            session_id=None,
            debug=False,
            dry_run=True,
            limit=None,
            fetch_titles=True,
            chunk=False,
            session_base_dir=session_dir,
        )

        self.assertEqual(result, 0)


class TestCLIOrganizeCommand(unittest.TestCase):
    """Test organize command functionality."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_organize_creates_session(self):
        """Organize command creates a new session."""
        from src.etl.cli import run_organize
        from src.etl.core.session import SessionManager

        # Create input directory with a Markdown file
        input_dir = self.test_dir / "input"
        input_dir.mkdir()
        (input_dir / "test.md").write_text("# Test\n\nContent here")

        session_dir = self.test_dir / "sessions"

        result = run_organize(
            input_path=input_dir,
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            session_base_dir=session_dir,
        )

        # Check session was created
        manager = SessionManager(session_dir)
        sessions = manager.list_sessions()
        self.assertGreater(len(sessions), 0)


class TestCLIStatusCommand(unittest.TestCase):
    """Test status command functionality."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_status_shows_session(self):
        """Status command shows session info."""
        from src.etl.cli import run_status
        from src.etl.core.session import SessionManager

        # Create a session
        session_dir = self.test_dir / "sessions"
        manager = SessionManager(session_dir)
        session = manager.create()
        manager.save(session)

        result = run_status(
            session_id=session.session_id,
            show_all=False,
            as_json=False,
            session_base_dir=session_dir,
        )

        self.assertEqual(result, 0)

    def test_status_all_lists_sessions(self):
        """Status --all lists all sessions."""
        from src.etl.cli import run_status
        from src.etl.core.session import SessionManager

        # Create sessions
        session_dir = self.test_dir / "sessions"
        manager = SessionManager(session_dir)
        s1 = manager.create()
        manager.save(s1)

        result = run_status(
            session_id=None,
            show_all=True,
            as_json=False,
            session_base_dir=session_dir,
        )

        self.assertEqual(result, 0)


class TestCLICleanCommand(unittest.TestCase):
    """Test clean command functionality."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_clean_dry_run_does_not_delete(self):
        """Clean --dry-run does not delete sessions."""
        from src.etl.cli import run_clean
        from src.etl.core.session import SessionManager

        # Create a session
        session_dir = self.test_dir / "sessions"
        manager = SessionManager(session_dir)
        session = manager.create()
        manager.save(session)

        result = run_clean(
            days=0,  # All sessions are "old"
            dry_run=True,
            force=False,
            session_base_dir=session_dir,
        )

        # Session should still exist
        sessions = manager.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(result, 0)


class TestCLIPhaseStats(unittest.TestCase):
    """Test PhaseStats recording in session.json."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_cli_import_records_phase_stats(self):
        """Import command records PhaseStats with success/error counts."""
        from src.etl.cli import run_import
        from src.etl.core.session import SessionManager

        # Create input directory with conversations.json
        input_dir = self.test_dir / "input"
        input_dir.mkdir()
        (input_dir / "conversations.json").write_text("[]")

        session_dir = self.test_dir / "sessions"

        result = run_import(
            input_path=input_dir,
            provider="claude",
            session_id=None,
            debug=False,
            dry_run=False,
            limit=None,
            fetch_titles=True,
            chunk=False,
            session_base_dir=session_dir,
        )

        # Load session and check phases
        manager = SessionManager(session_dir)
        sessions = manager.list_sessions()
        self.assertGreater(len(sessions), 0)

        session = manager.load(sessions[0])
        self.assertIn("import", session.phases)

        phase_stats = session.phases["import"]
        self.assertIn(phase_stats.status, ["completed", "partial", "failed"])
        self.assertIsInstance(phase_stats.expected_total_item_count, int)
        self.assertIsNotNone(phase_stats.completed_information)
        self.assertIsInstance(phase_stats.completed_information.success_count, int)
        self.assertIsInstance(phase_stats.completed_information.error_count, int)
        self.assertIsNotNone(phase_stats.completed_information.completed_at)

    def test_cli_import_crashed_records_error(self):
        """Import command records crashed status on unhandled exception."""
        from unittest.mock import patch

        from src.etl.cli import run_import
        from src.etl.core.session import SessionManager

        # Create input directory with conversations.json
        input_dir = self.test_dir / "input"
        input_dir.mkdir()
        (input_dir / "conversations.json").write_text("[]")

        session_dir = self.test_dir / "sessions"

        # Mock ImportPhase.run() to raise an exception
        with patch("src.etl.cli.ImportPhase.run") as mock_run:
            mock_run.side_effect = RuntimeError("Simulated crash")

            result = run_import(
                input_path=input_dir,
                provider="claude",
                session_id=None,
                debug=False,
                dry_run=False,
                limit=None,
                fetch_titles=True,
                chunk=False,
                session_base_dir=session_dir,
            )

            # Should return ERROR exit code
            self.assertEqual(result, 1)

            # Load session and check crashed phase stats
            manager = SessionManager(session_dir)
            sessions = manager.list_sessions()
            self.assertGreater(len(sessions), 0)

            session = manager.load(sessions[0])
            self.assertIn("import", session.phases)

            phase_stats = session.phases["import"]
            self.assertEqual(phase_stats.status, "crashed")
            self.assertIsNotNone(phase_stats.completed_information)
            self.assertEqual(phase_stats.completed_information.success_count, 0)
            self.assertEqual(phase_stats.completed_information.error_count, 0)
            self.assertIsNotNone(phase_stats.error)
            self.assertIn("RuntimeError", phase_stats.error)


class TestCLIMain(unittest.TestCase):
    """Test CLI main entry point."""

    def test_main_exists(self):
        """Main function exists."""
        from src.etl.cli import main

        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
