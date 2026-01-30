"""Unit tests for import command module.

Demonstrates improved testability of modular CLI structure.
Tests command logic without full CLI invocation.
"""

import unittest
from argparse import ArgumentParser, Namespace
from pathlib import Path

from src.etl.cli.commands import import_cmd
from src.etl.cli.common import ExitCode


class TestImportCommandValidation(unittest.TestCase):
    """Test import command input validation."""

    def test_import_nonexistent_input(self):
        """Test import command with nonexistent input path.

        Verifies that the command returns INPUT_NOT_FOUND exit code
        when given a path that doesn't exist.
        """
        # Arrange: Create args with nonexistent path
        args = Namespace(
            input=Path("/nonexistent/path/to/data"),
            provider="claude",
            session=None,
            debug=False,
            dry_run=False,
            limit=None,
            no_fetch_titles=False,
            chunk=False,
        )

        # Act: Execute command
        exit_code = import_cmd.execute(args)

        # Assert: Should return INPUT_NOT_FOUND
        self.assertEqual(
            exit_code,
            ExitCode.INPUT_NOT_FOUND,
            "Import should return INPUT_NOT_FOUND for nonexistent input",
        )


class TestImportCommandRegistration(unittest.TestCase):
    """Test import command argument registration."""

    def test_import_help_registration(self):
        """Test that import command registers correctly with argparse.

        Verifies that:
        1. Command name is 'import'
        2. Required --input argument is registered
        3. Optional --provider argument is registered with choices
        4. Default values are set correctly
        """
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")

        # Act: Register import command
        import_cmd.register(subparsers)

        # Assert: Parse test arguments
        args = parser.parse_args(["import", "--input", "/test/path"])

        self.assertEqual(args.command, "import", "Command should be 'import'")
        self.assertEqual(args.input, "/test/path", "--input should be parsed")
        self.assertEqual(args.provider, "claude", "--provider default should be 'claude'")

    def test_import_provider_choices(self):
        """Test that --provider argument validates choices correctly."""
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")
        import_cmd.register(subparsers)

        # Act & Assert: Valid providers
        valid_providers = ["claude", "openai", "github"]
        for provider in valid_providers:
            args = parser.parse_args(["import", "--input", "/test/path", "--provider", provider])
            self.assertEqual(args.provider, provider, f"--provider should accept '{provider}'")

        # Act & Assert: Invalid provider should raise error
        with self.assertRaises(SystemExit):
            parser.parse_args(["import", "--input", "/test/path", "--provider", "invalid"])

    def test_import_required_arguments(self):
        """Test that --input is required."""
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")
        import_cmd.register(subparsers)

        # Act & Assert: Missing --input should raise error
        with self.assertRaises(SystemExit):
            parser.parse_args(["import"])


class TestImportCommandDryRun(unittest.TestCase):
    """Test import command dry-run functionality."""

    def test_import_dry_run_flag(self):
        """Test that --dry-run flag is recognized."""
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")
        import_cmd.register(subparsers)

        # Act: Parse with --dry-run
        args = parser.parse_args(["import", "--input", "/test/path", "--dry-run"])

        # Assert: dry_run should be True
        self.assertTrue(args.dry_run, "--dry-run should set dry_run=True")

        # Act: Parse without --dry-run
        args = parser.parse_args(["import", "--input", "/test/path"])

        # Assert: dry_run should be False
        self.assertFalse(args.dry_run, "dry_run should default to False")


if __name__ == "__main__":
    unittest.main()
