"""Tests for Vault Output pipeline nodes.

Phase 2 (US1 Preview) tests verify:
- Genre to Vault mapping (ai -> engineer Vault)
- Topic subfolder resolution
- Empty topic handling (Vault root placement)
- Topic sanitization (special characters)
- Conflict detection (existing files)
- No-conflict detection
- Preview summary output format

Phase 3 (US2+US3 Copy) tests verify:
- File copy to vault creates destination file
- Subdirectory creation during copy
- Skip existing files (default conflict handling)
- Copy summary output format
- Permission error handling (skip, not crash)

Phase 4 (US4 Overwrite) tests verify:
- Overwrite mode replaces existing file content
- Overwrite mode returns "overwritten" status

Phase 5 (US5 Increment) tests verify:
- find_incremented_path returns file_1.md when file.md exists
- find_incremented_path returns file_2.md when file.md and file_1.md exist
- Increment mode creates file_1.md when original exists
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from obsidian_etl.pipelines.vault_output.nodes import (
    check_conflicts,
    copy_to_vault,
    find_incremented_path,
    log_copy_summary,
    log_preview_summary,
    resolve_vault_destination,
    sanitize_topic,
)


def _make_vault_params() -> dict:
    """Helper to create vault output params matching parameters.yml."""
    return {
        "vault_base_path": "/home/takuya/Documents/Obsidian/Vaults",
        "genre_vault_mapping": {
            "ai": "エンジニア",
            "devops": "エンジニア",
            "engineer": "エンジニア",
            "business": "ビジネス",
            "economy": "経済",
            "health": "日常",
            "parenting": "日常",
            "travel": "日常",
            "lifestyle": "日常",
            "daily": "日常",
            "other": "その他",
        },
        "conflict_handling": "skip",
    }


def _make_organized_content(
    title: str = "Test Note",
    genre: str = "ai",
    topic: str = "python",
) -> str:
    """Helper to create organized markdown content with frontmatter."""
    return (
        "---\n"
        f"title: {title}\n"
        f"genre: {genre}\n"
        f"topic: {topic}\n"
        "created: 2026-01-15\n"
        "tags:\n"
        "  - test\n"
        "normalized: true\n"
        "file_id: abc123\n"
        "---\n"
        "\n"
        "## Content\n"
        "\n"
        "Test content here.\n"
    )


class TestResolveVaultDestination(unittest.TestCase):
    """resolve_vault_destination: genre -> Vault mapping and path construction."""

    def setUp(self):
        """Set up common test parameters."""
        self.params = _make_vault_params()

    def test_resolve_vault_destination_ai_to_engineer(self):
        """genre=ai のファイルが エンジニア Vault にマッピングされること。"""
        organized_files = {
            "note1": _make_organized_content(title="AI Note", genre="ai", topic="machine-learning"),
        }

        result = resolve_vault_destination(organized_files, self.params)

        self.assertIn("note1", result)
        dest = result["note1"]
        self.assertEqual(dest["vault_name"], "エンジニア")
        expected_path = Path(
            "/home/takuya/Documents/Obsidian/Vaults/エンジニア/machine-learning/AI Note.md"
        )
        self.assertEqual(Path(dest["full_path"]), expected_path)

    def test_resolve_vault_destination_with_topic_subfolder(self):
        """topic が指定されている場合、サブフォルダとしてパスに含まれること。"""
        organized_files = {
            "note1": _make_organized_content(title="Docker Guide", genre="devops", topic="docker"),
        }

        result = resolve_vault_destination(organized_files, self.params)

        dest = result["note1"]
        self.assertEqual(dest["vault_name"], "エンジニア")
        self.assertEqual(dest["subfolder"], "docker")
        full_path = Path(dest["full_path"])
        self.assertIn("docker", str(full_path))
        self.assertTrue(str(full_path).endswith("Docker Guide.md"))

    def test_resolve_vault_destination_empty_topic(self):
        """topic が空の場合、Vault 直下にファイルが配置されること。"""
        organized_files = {
            "note1": _make_organized_content(title="General Note", genre="business", topic=""),
        }

        result = resolve_vault_destination(organized_files, self.params)

        dest = result["note1"]
        self.assertEqual(dest["vault_name"], "ビジネス")
        expected_path = Path("/home/takuya/Documents/Obsidian/Vaults/ビジネス/General Note.md")
        self.assertEqual(Path(dest["full_path"]), expected_path)
        # subfolder should be empty/None
        self.assertFalse(dest.get("subfolder"))


class TestSanitizeTopic(unittest.TestCase):
    """sanitize_topic: special characters in topic are replaced."""

    def test_sanitize_topic_special_chars(self):
        """スラッシュ、バックスラッシュがアンダースコアに置換されること。"""
        self.assertEqual(sanitize_topic("CI/CD"), "CI_CD")
        self.assertEqual(sanitize_topic("path\\to"), "path_to")
        self.assertEqual(sanitize_topic("CI/CD\\pipeline"), "CI_CD_pipeline")

    def test_sanitize_topic_empty(self):
        """空文字列はそのまま返されること。"""
        self.assertEqual(sanitize_topic(""), "")

    def test_sanitize_topic_normal(self):
        """通常の文字列はそのまま返されること。"""
        self.assertEqual(sanitize_topic("python"), "python")

    def test_sanitize_topic_strips_whitespace(self):
        """先頭・末尾の空白が除去されること。"""
        self.assertEqual(sanitize_topic("  python  "), "python")

    def test_sanitize_topic_unicode(self):
        """日本語トピックがそのまま返されること。"""
        self.assertEqual(sanitize_topic("機械学習"), "機械学習")


class TestCheckConflicts(unittest.TestCase):
    """check_conflicts: detect existing files at destination paths."""

    def test_check_conflicts_detects_existing_file(self):
        """出力先に既存ファイルがある場合、競合が検出されること。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an existing file at the destination
            vault_dir = Path(tmpdir) / "エンジニア" / "python"
            vault_dir.mkdir(parents=True)
            existing_file = vault_dir / "Existing Note.md"
            existing_file.write_text("old content", encoding="utf-8")

            destinations = {
                "note1": {
                    "vault_name": "エンジニア",
                    "subfolder": "python",
                    "file_name": "Existing Note.md",
                    "full_path": str(existing_file),
                },
            }

            conflicts = check_conflicts(destinations)

            self.assertEqual(len(conflicts), 1)
            conflict = conflicts[0]
            self.assertEqual(conflict["conflict_type"], "exists")
            self.assertEqual(conflict["destination"], str(existing_file))
            self.assertGreater(conflict["existing_size"], 0)

    def test_check_conflicts_no_conflict(self):
        """出力先にファイルが存在しない場合、競合が検出されないこと。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existing_path = Path(tmpdir) / "エンジニア" / "python" / "New Note.md"

            destinations = {
                "note1": {
                    "vault_name": "エンジニア",
                    "subfolder": "python",
                    "file_name": "New Note.md",
                    "full_path": str(non_existing_path),
                },
            }

            conflicts = check_conflicts(destinations)

            self.assertEqual(len(conflicts), 0)


class TestLogPreviewSummary(unittest.TestCase):
    """log_preview_summary: output format for preview information."""

    def test_log_preview_summary_output_format(self):
        """Preview サマリーが正しい形式で返されること。"""
        destinations = {
            "note1": {
                "vault_name": "エンジニア",
                "subfolder": "python",
                "file_name": "Note1.md",
                "full_path": "/vaults/エンジニア/python/Note1.md",
            },
            "note2": {
                "vault_name": "エンジニア",
                "subfolder": "docker",
                "file_name": "Note2.md",
                "full_path": "/vaults/エンジニア/docker/Note2.md",
            },
            "note3": {
                "vault_name": "ビジネス",
                "subfolder": "",
                "file_name": "Note3.md",
                "full_path": "/vaults/ビジネス/Note3.md",
            },
        }
        conflicts = [
            {
                "source_file": "note1",
                "destination": "/vaults/エンジニア/python/Note1.md",
                "conflict_type": "exists",
            }
        ]

        result = log_preview_summary(destinations, conflicts)

        # Should return a summary dict with key information
        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_files"], 3)
        self.assertEqual(result["total_conflicts"], 1)
        # Genre distribution should show counts per vault
        self.assertIn("vault_distribution", result)
        self.assertEqual(result["vault_distribution"]["エンジニア"], 2)
        self.assertEqual(result["vault_distribution"]["ビジネス"], 1)


class TestCopyToVault(unittest.TestCase):
    """copy_to_vault: file copy with conflict handling (US2+US3)."""

    def setUp(self):
        """Set up temp directories for source and destination."""
        self.source_dir = tempfile.mkdtemp()
        self.vault_dir = tempfile.mkdtemp()
        self.params = _make_vault_params()
        self.params["vault_base_path"] = self.vault_dir

    def tearDown(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.vault_dir, ignore_errors=True)

    def _write_source(self, name: str, content: str) -> Path:
        """Helper to write a source file."""
        path = Path(self.source_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_copy_to_vault_creates_file(self):
        """ファイルが Vault の正しい位置にコピーされること。"""
        content = _make_organized_content(title="AI Note", genre="ai", topic="python")
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        results = copy_to_vault(organized_files, destinations, self.params)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["status"], "copied")
        # Verify file actually exists at destination
        dest_path = Path(result["destination"])
        self.assertTrue(dest_path.exists())
        # Verify content matches
        copied_content = dest_path.read_text(encoding="utf-8")
        self.assertEqual(copied_content, content)

    def test_copy_to_vault_creates_subfolder(self):
        """コピー時にサブフォルダが自動作成されること。"""
        content = _make_organized_content(
            title="Docker Guide", genre="devops", topic="docker/compose"
        )
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        # Subfolder should not exist yet
        dest_path = Path(destinations["note1"]["full_path"])
        self.assertFalse(dest_path.parent.exists())

        results = copy_to_vault(organized_files, destinations, self.params)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "copied")
        # Verify subfolder was created
        self.assertTrue(dest_path.parent.exists())
        self.assertTrue(dest_path.exists())

    def test_copy_to_vault_skip_existing(self):
        """既存ファイルがある場合、skip モードではスキップされること（US3）。"""
        content = _make_organized_content(title="Existing Note", genre="ai", topic="python")
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        # Pre-create the destination file with different content
        dest_path = Path(destinations["note1"]["full_path"])
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        original_content = "original content that should be preserved"
        dest_path.write_text(original_content, encoding="utf-8")

        # conflict_handling defaults to "skip"
        results = copy_to_vault(organized_files, destinations, self.params)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["status"], "skipped")
        self.assertIsNone(result["destination"])
        # Verify original file was NOT overwritten
        preserved_content = dest_path.read_text(encoding="utf-8")
        self.assertEqual(preserved_content, original_content)

    def test_copy_to_vault_overwrite_existing(self):
        """overwrite モードで既存ファイルが新しい内容に上書きされること（US4）。"""
        content = _make_organized_content(title="Updated Note", genre="ai", topic="python")
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        # Pre-create the destination file with old content
        dest_path = Path(destinations["note1"]["full_path"])
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        old_content = "old content that should be replaced"
        dest_path.write_text(old_content, encoding="utf-8")

        # Set conflict_handling to "overwrite"
        overwrite_params = dict(self.params)
        overwrite_params["conflict_handling"] = "overwrite"

        results = copy_to_vault(organized_files, destinations, overwrite_params)

        self.assertEqual(len(results), 1)
        result = results[0]
        # Should report "overwritten" status (not "copied" or "skipped")
        self.assertEqual(result["status"], "overwritten")
        self.assertIsNotNone(result["destination"])
        # Verify file was actually overwritten with new content
        actual_content = dest_path.read_text(encoding="utf-8")
        self.assertEqual(actual_content, content)
        self.assertNotEqual(actual_content, old_content)

    def test_handle_conflict_overwrite_mode(self):
        """overwrite モードでコピーサマリーに overwritten カウントが含まれること（US4）。"""
        copy_results = [
            {
                "source": "note1",
                "destination": "/vaults/エンジニア/python/Note1.md",
                "status": "overwritten",
                "error_message": None,
            },
            {
                "source": "note2",
                "destination": "/vaults/エンジニア/docker/Note2.md",
                "status": "copied",
                "error_message": None,
            },
            {
                "source": "note3",
                "destination": None,
                "status": "skipped",
                "error_message": None,
            },
        ]

        result = log_copy_summary(copy_results)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["copied"], 1)
        self.assertEqual(result["skipped"], 1)
        # Should include overwritten count
        self.assertIn("overwritten", result)
        self.assertEqual(result["overwritten"], 1)

    def test_copy_to_vault_permission_error_skips(self):
        """パーミッションエラー時にエラーステータスで返し、例外を投げないこと。"""
        content = _make_organized_content(title="Permission Test", genre="ai", topic="python")
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        # Create parent dir as read-only to cause permission error
        dest_path = Path(destinations["note1"]["full_path"])
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(str(dest_path.parent), 0o444)

        try:
            results = copy_to_vault(organized_files, destinations, self.params)

            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result["status"], "error")
            self.assertIsNotNone(result["error_message"])
        finally:
            # Restore permissions for cleanup
            os.chmod(str(dest_path.parent), 0o755)


class TestLogCopySummary(unittest.TestCase):
    """log_copy_summary: output format for copy results (US2)."""

    def test_log_copy_summary_output_format(self):
        """コピーサマリーが正しい形式で返されること。"""
        copy_results = [
            {
                "source": "note1",
                "destination": "/vaults/エンジニア/python/Note1.md",
                "status": "copied",
                "error_message": None,
            },
            {
                "source": "note2",
                "destination": None,
                "status": "skipped",
                "error_message": None,
            },
            {
                "source": "note3",
                "destination": "/vaults/ビジネス/Note3.md",
                "status": "copied",
                "error_message": None,
            },
            {
                "source": "note4",
                "destination": None,
                "status": "error",
                "error_message": "Permission denied",
            },
        ]

        result = log_copy_summary(copy_results)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["copied"], 2)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["errors"], 1)


class TestFindIncrementedPath(unittest.TestCase):
    """find_incremented_path: next available incremented file path (US5)."""

    def test_find_incremented_path_first(self):
        """file.md が存在し file_1.md が存在しない場合、file_1.md を返すこと。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "Note.md"
            existing.write_text("existing content", encoding="utf-8")

            result = find_incremented_path(existing)

            expected = Path(tmpdir) / "Note_1.md"
            self.assertEqual(result, expected)
            # The original file should still exist
            self.assertTrue(existing.exists())
            # The incremented path should NOT exist yet (just returns the path)
            self.assertFalse(result.exists())

    def test_find_incremented_path_second(self):
        """file.md と file_1.md が存在する場合、file_2.md を返すこと。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "Note.md"
            existing.write_text("existing content", encoding="utf-8")
            first_increment = Path(tmpdir) / "Note_1.md"
            first_increment.write_text("first increment", encoding="utf-8")

            result = find_incremented_path(existing)

            expected = Path(tmpdir) / "Note_2.md"
            self.assertEqual(result, expected)
            self.assertFalse(result.exists())


class TestCopyToVaultIncrement(unittest.TestCase):
    """copy_to_vault with increment mode (US5)."""

    def setUp(self):
        """Set up temp directories for source and destination."""
        self.source_dir = tempfile.mkdtemp()
        self.vault_dir = tempfile.mkdtemp()
        self.params = _make_vault_params()
        self.params["vault_base_path"] = self.vault_dir
        self.params["conflict_handling"] = "increment"

    def tearDown(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.vault_dir, ignore_errors=True)

    def test_copy_to_vault_increment_existing(self):
        """increment モードで既存ファイルがある場合、file_1.md として保存されること。"""
        content = _make_organized_content(title="My Note", genre="ai", topic="python")
        organized_files = {"note1": content}

        destinations = resolve_vault_destination(organized_files, self.params)

        # Pre-create the destination file with old content
        dest_path = Path(destinations["note1"]["full_path"])
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        old_content = "original content that should be preserved"
        dest_path.write_text(old_content, encoding="utf-8")

        results = copy_to_vault(organized_files, destinations, self.params)

        self.assertEqual(len(results), 1)
        result = results[0]
        # Should report "incremented" status
        self.assertEqual(result["status"], "incremented")
        self.assertIsNotNone(result["destination"])
        # Destination should be file_1.md, not the original
        incremented_path = Path(result["destination"])
        self.assertTrue(incremented_path.name.endswith("_1.md"))
        self.assertTrue(incremented_path.exists())
        # Verify new content was written to incremented path
        actual_content = incremented_path.read_text(encoding="utf-8")
        self.assertEqual(actual_content, content)
        # Verify original file was NOT modified
        preserved_content = dest_path.read_text(encoding="utf-8")
        self.assertEqual(preserved_content, old_content)


if __name__ == "__main__":
    unittest.main()
