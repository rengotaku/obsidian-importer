"""Tests for import command CLI input interface unification (US4).

Tests for:
- --input-type path (default) backward compatibility
- --input-type url saves URL to extract/input/url.txt
- --input multiple values (action="append")
- URL input without --input-type raises error

These tests verify Phase 6 (US4) requirements:
- CLI supports --input-type argument (path/url)
- --input is repeatable (action="append")
- URL inputs are saved to url.txt
- Input validation rejects URL without --input-type url
"""

import argparse
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.cli import create_parser
from src.etl.cli.commands import import_cmd


class TestInputTypePathDefault(unittest.TestCase):
    """--input-type path がデフォルトで従来と同じ動作をする."""

    def test_input_type_defaults_to_path(self):
        """--input-type 省略時にデフォルト値が 'path' になる."""
        parser = create_parser()
        args = parser.parse_args(["import", "--input", "/path/to/data", "--provider", "claude"])
        self.assertEqual(args.input_type, "path")

    def test_input_type_path_explicit(self):
        """--input-type path を明示指定できる."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "import",
                "--input",
                "/path/to/data",
                "--input-type",
                "path",
                "--provider",
                "claude",
            ]
        )
        self.assertEqual(args.input_type, "path")

    def test_input_type_path_copies_files_to_extract_input(self):
        """--input-type path でファイルが extract/input/ にコピーされる（従来動作）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a fake input file
            input_dir = tmpdir / "input"
            input_dir.mkdir()
            input_file = input_dir / "conversations.json"
            input_file.write_text('{"conversations": []}', encoding="utf-8")

            # Create session base dir
            session_base = tmpdir / "sessions"
            session_base.mkdir()

            args = argparse.Namespace(
                input=[str(input_dir)],  # list (action="append")
                input_type="path",
                provider="claude",
                session=None,
                debug=False,
                dry_run=True,  # dry-run to avoid full execution
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            # Should not raise - path type with valid path
            result = import_cmd.execute(args)
            # dry-run should succeed (exit code 0)
            self.assertEqual(result, 0)


class TestInputTypeUrl(unittest.TestCase):
    """--input-type url で URL が extract/input/url.txt に保存される."""

    def test_input_type_url_accepted(self):
        """--input-type url がパーサーに受け入れられる."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "import",
                "--input",
                "https://github.com/user/repo/tree/master/_posts",
                "--input-type",
                "url",
                "--provider",
                "github",
            ]
        )
        self.assertEqual(args.input_type, "url")

    def test_input_type_url_saves_to_url_txt(self):
        """--input-type url で URL が extract/input/url.txt に保存される."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            session_base = tmpdir / "sessions"
            session_base.mkdir()

            url = "https://github.com/user/repo/tree/master/_posts"

            args = argparse.Namespace(
                input=[url],  # list (action="append")
                input_type="url",
                provider="github",
                session=None,
                debug=False,
                dry_run=False,
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            # Execute and check that url.txt was created
            with patch.object(import_cmd, "ImportPhase") as mock_phase_cls:
                mock_phase = MagicMock()
                mock_phase.run.return_value = MagicMock(
                    items_processed=0,
                    items_failed=0,
                    items_skipped=0,
                    status=MagicMock(value="completed"),
                )
                mock_phase_cls.return_value = mock_phase

                import_cmd.execute(args)

            # Find the session directory that was created
            session_dirs = list(session_base.glob("*/import/extract/input"))
            self.assertTrue(
                len(session_dirs) > 0,
                "extract/input directory should be created",
            )

            extract_input = session_dirs[0]
            url_file = extract_input / "url.txt"
            self.assertTrue(
                url_file.exists(),
                "url.txt should be created for --input-type url",
            )
            self.assertEqual(
                url_file.read_text(encoding="utf-8").strip(),
                url,
                "url.txt should contain the URL string",
            )

    def test_input_type_url_not_github_url_txt(self):
        """url.txt のファイル名は 'url.txt' であり 'github_url.txt' ではない."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            session_base = tmpdir / "sessions"
            session_base.mkdir()

            url = "https://github.com/user/repo/tree/master/_posts"

            args = argparse.Namespace(
                input=[url],
                input_type="url",
                provider="github",
                session=None,
                debug=False,
                dry_run=False,
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            with patch.object(import_cmd, "ImportPhase") as mock_phase_cls:
                mock_phase = MagicMock()
                mock_phase.run.return_value = MagicMock(
                    items_processed=0,
                    items_failed=0,
                    items_skipped=0,
                    status=MagicMock(value="completed"),
                )
                mock_phase_cls.return_value = mock_phase

                import_cmd.execute(args)

            # The new contract uses url.txt, not github_url.txt
            session_dirs = list(session_base.glob("*/import/extract/input"))
            if session_dirs:
                extract_input = session_dirs[0]
                # url.txt should exist (new contract)
                self.assertTrue(
                    (extract_input / "url.txt").exists(),
                    "New contract uses 'url.txt' not 'github_url.txt'",
                )


class TestMultipleInputs(unittest.TestCase):
    """--input 複数指定で全入力が処理される."""

    def test_input_is_repeatable(self):
        """--input を複数回指定でき、リストとして保持される."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "import",
                "--input",
                "export1.zip",
                "--input",
                "export2.zip",
                "--provider",
                "openai",
            ]
        )
        self.assertIsInstance(args.input, list)
        self.assertEqual(len(args.input), 2)
        self.assertEqual(args.input[0], "export1.zip")
        self.assertEqual(args.input[1], "export2.zip")

    def test_single_input_is_also_list(self):
        """--input を 1 回だけ指定してもリストとして保持される."""
        parser = create_parser()
        args = parser.parse_args(["import", "--input", "/path/to/data", "--provider", "claude"])
        self.assertIsInstance(args.input, list)
        self.assertEqual(len(args.input), 1)
        self.assertEqual(args.input[0], "/path/to/data")

    def test_multiple_inputs_all_copied(self):
        """複数 --input で全入力ファイルが extract/input/ にコピーされる."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create two fake ZIP files
            zip1 = tmpdir / "export1.zip"
            zip2 = tmpdir / "export2.zip"
            zip1.write_bytes(b"PK\x03\x04fake_zip1")
            zip2.write_bytes(b"PK\x03\x04fake_zip2")

            session_base = tmpdir / "sessions"
            session_base.mkdir()

            args = argparse.Namespace(
                input=[str(zip1), str(zip2)],
                input_type="path",
                provider="openai",
                session=None,
                debug=False,
                dry_run=False,
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            with patch.object(import_cmd, "ImportPhase") as mock_phase_cls:
                mock_phase = MagicMock()
                mock_phase.run.return_value = MagicMock(
                    items_processed=0,
                    items_failed=0,
                    items_skipped=0,
                    status=MagicMock(value="completed"),
                )
                mock_phase_cls.return_value = mock_phase

                import_cmd.execute(args)

            # Check that both files were copied to extract/input/
            session_dirs = list(session_base.glob("*/import/extract/input"))
            self.assertTrue(len(session_dirs) > 0)
            extract_input = session_dirs[0]

            copied_files = list(extract_input.iterdir())
            zip_names = {f.name for f in copied_files}
            self.assertIn(
                "export1.zip",
                zip_names,
                "First input should be copied to extract/input/",
            )
            self.assertIn(
                "export2.zip",
                zip_names,
                "Second input should be copied to extract/input/",
            )


class TestUrlWithoutInputTypeError(unittest.TestCase):
    """--input-type 省略で URL 入力はエラーになる."""

    def test_url_without_input_type_fails_path_validation(self):
        """URL を --input-type なし（デフォルト path）で指定するとエラー."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            session_base = tmpdir / "sessions"
            session_base.mkdir()

            # URL input without --input-type (defaults to "path")
            args = argparse.Namespace(
                input=["https://github.com/user/repo/tree/master/_posts"],
                input_type="path",  # default
                provider="github",
                session=None,
                debug=False,
                dry_run=False,
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            result = import_cmd.execute(args)

            # Should fail because URL is not a valid local path
            self.assertNotEqual(
                result,
                0,
                "URL input with input_type='path' should return error exit code",
            )

    def test_url_input_type_path_gives_input_not_found(self):
        """URL を path タイプで渡すと INPUT_NOT_FOUND エラーコードを返す."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            session_base = tmpdir / "sessions"
            session_base.mkdir()

            args = argparse.Namespace(
                input=["https://github.com/user/repo/tree/master/_posts"],
                input_type="path",
                provider="github",
                session=None,
                debug=False,
                dry_run=False,
                limit=None,
                no_fetch_titles=True,
                chunk=False,
                _session_base_dir=session_base,
            )

            # Capture stderr
            with patch("sys.stderr", new_callable=io.StringIO):
                result = import_cmd.execute(args)

            # ExitCode.INPUT_NOT_FOUND = 2
            from src.etl.cli.common import ExitCode

            self.assertEqual(
                result,
                ExitCode.INPUT_NOT_FOUND,
                "URL with input_type='path' should return INPUT_NOT_FOUND",
            )

    def test_input_type_choices_are_path_and_url(self):
        """--input-type は 'path' と 'url' のみ受け付ける."""
        parser = create_parser()

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stderr", new_callable=io.StringIO):
                parser.parse_args(
                    [
                        "import",
                        "--input",
                        "/path",
                        "--input-type",
                        "invalid",
                        "--provider",
                        "claude",
                    ]
                )
        self.assertEqual(ctx.exception.code, 2)  # argparse error


if __name__ == "__main__":
    unittest.main()
