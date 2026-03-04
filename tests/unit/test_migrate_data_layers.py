"""Tests for data layer migration script.

Phase 3 RED tests: Verify migration script moves JSON files from
07_model_output/ to 05_model_input/ correctly.

These tests validate FR-004, FR-005 from spec.md (User Story 2).

Test Strategy:
- Use tempfile to create isolated directory structures
- Test migration function with various scenarios
- Tests will FAIL (RED) because scripts/migrate_data_layers.py does not exist yet
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import will fail until the migration script is created
from scripts.migrate_data_layers import MigrationResult, migrate_json_to_model_input

# Subdirectories that should be migrated (JSON only)
_MIGRATION_SUBDIRS = [
    "classified",
    "cleaned",
    "normalized",
    "topic_extracted",
    "vault_determined",
    "organized",
]


def _create_json_file(directory: Path, filename: str, content: dict | None = None):
    """Create a JSON file in the given directory."""
    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / filename
    data = content if content is not None else {"file_id": "test123", "data": "sample"}
    filepath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return filepath


class TestMigrateNoFiles(unittest.TestCase):
    """移行元にファイルがない場合のテスト (T025)。"""

    def setUp(self):
        """一時ディレクトリを作成。"""
        self.tmpdir = tempfile.mkdtemp()
        self.source_base = Path(self.tmpdir) / "data" / "07_model_output"
        self.target_base = Path(self.tmpdir) / "data" / "05_model_input"
        # Create empty source subdirectories
        for subdir in _MIGRATION_SUBDIRS:
            (self.source_base / subdir).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """一時ディレクトリを削除。"""
        shutil.rmtree(self.tmpdir)

    def test_no_files_returns_zero_migrated(self):
        """移行元にファイルがない場合、migrated が 0 であること。"""
        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertIsInstance(result, MigrationResult)
        self.assertEqual(result.migrated, 0)

    def test_no_files_returns_zero_skipped(self):
        """移行元にファイルがない場合、skipped が 0 であること。"""
        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.skipped, 0)

    def test_no_files_returns_empty_errors(self):
        """移行元にファイルがない場合、errors が空リストであること。"""
        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.errors, [])

    def test_source_dir_not_exist_returns_zero(self):
        """移行元ディレクトリが存在しない場合、migrated が 0 であること。"""
        nonexistent = Path(self.tmpdir) / "nonexistent"
        result = migrate_json_to_model_input(
            source_base=nonexistent,
            target_base=self.target_base,
        )
        self.assertEqual(result.migrated, 0)
        self.assertEqual(result.skipped, 0)


class TestMigrateJsonFiles(unittest.TestCase):
    """JSON ファイル移行テスト (T026)。"""

    def setUp(self):
        """テスト用ディレクトリ構造を作成。"""
        self.tmpdir = tempfile.mkdtemp()
        self.source_base = Path(self.tmpdir) / "data" / "07_model_output"
        self.target_base = Path(self.tmpdir) / "data" / "05_model_input"

    def tearDown(self):
        """一時ディレクトリを削除。"""
        shutil.rmtree(self.tmpdir)

    def test_single_json_file_migrated(self):
        """1つの JSON ファイルが移行先に移動されること。"""
        _create_json_file(
            self.source_base / "classified",
            "item1.json",
            {"file_id": "abc", "genre": "AI"},
        )
        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.migrated, 1)
        # Verify file exists at target
        target_file = self.target_base / "classified" / "item1.json"
        self.assertTrue(target_file.exists(), f"Expected {target_file} to exist")

    def test_source_file_removed_after_migration(self):
        """移行後、移行元のファイルが削除されること。"""
        source_file = _create_json_file(
            self.source_base / "normalized",
            "item2.json",
        )
        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertFalse(source_file.exists(), "Source file should be removed after migration")

    def test_multiple_subdirs_migrated(self):
        """複数サブディレクトリの JSON が移行されること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.source_base / "cleaned", "b.json")
        _create_json_file(self.source_base / "normalized", "c.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.migrated, 3)

        self.assertTrue((self.target_base / "classified" / "a.json").exists())
        self.assertTrue((self.target_base / "cleaned" / "b.json").exists())
        self.assertTrue((self.target_base / "normalized" / "c.json").exists())

    def test_json_content_preserved_after_migration(self):
        """移行後、JSON の内容が変更されていないこと。"""
        original_data = {"file_id": "xyz", "genre": "DevOps", "confidence": 0.95}
        _create_json_file(
            self.source_base / "classified",
            "preserve.json",
            original_data,
        )
        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        target_file = self.target_base / "classified" / "preserve.json"
        with open(target_file, encoding="utf-8") as f:
            migrated_data = json.load(f)
        self.assertEqual(migrated_data, original_data)

    def test_md_files_not_migrated(self):
        """MD ファイルは移行対象外であること。"""
        # Create both JSON and MD in organized/
        _create_json_file(self.source_base / "organized", "item.json")
        md_file = self.source_base / "organized" / "note.md"
        md_file.write_text("# Test Note", encoding="utf-8")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        # Only JSON should be migrated
        self.assertEqual(result.migrated, 1)
        # MD file should remain in source
        self.assertTrue(md_file.exists(), "MD file should not be migrated")

    def test_target_dir_created_automatically(self):
        """移行先ディレクトリが存在しない場合、自動作成されること。"""
        _create_json_file(self.source_base / "topic_extracted", "item.json")
        # target_base does not exist yet
        self.assertFalse(self.target_base.exists())

        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertTrue((self.target_base / "topic_extracted").exists())


class TestMigrateSkipExisting(unittest.TestCase):
    """既存ファイルスキップテスト (T027)。"""

    def setUp(self):
        """テスト用ディレクトリ構造を作成。"""
        self.tmpdir = tempfile.mkdtemp()
        self.source_base = Path(self.tmpdir) / "data" / "07_model_output"
        self.target_base = Path(self.tmpdir) / "data" / "05_model_input"

    def tearDown(self):
        """一時ディレクトリを削除。"""
        shutil.rmtree(self.tmpdir)

    def test_existing_file_skipped(self):
        """移行先に同名ファイルが存在する場合、スキップされること。"""
        _create_json_file(
            self.source_base / "classified",
            "existing.json",
            {"version": "old"},
        )
        _create_json_file(
            self.target_base / "classified",
            "existing.json",
            {"version": "new"},
        )

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.migrated, 0)

    def test_existing_file_not_overwritten(self):
        """スキップ時、移行先の既存ファイルが上書きされないこと。"""
        _create_json_file(
            self.source_base / "classified",
            "keep.json",
            {"version": "old"},
        )
        _create_json_file(
            self.target_base / "classified",
            "keep.json",
            {"version": "new"},
        )

        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        target_file = self.target_base / "classified" / "keep.json"
        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["version"], "new", "Existing file should not be overwritten")

    def test_mixed_migrate_and_skip(self):
        """一部スキップ、一部移行の場合のカウントが正確であること。"""
        # File that will be skipped (already exists at target)
        _create_json_file(self.source_base / "classified", "skip.json", {"id": "1"})
        _create_json_file(self.target_base / "classified", "skip.json", {"id": "1"})
        # File that will be migrated (does not exist at target)
        _create_json_file(self.source_base / "classified", "new.json", {"id": "2"})

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.migrated, 1)
        self.assertEqual(result.skipped, 1)


class TestMigrationSummary(unittest.TestCase):
    """サマリー出力テスト (T028)。"""

    def setUp(self):
        """テスト用ディレクトリ構造を作成。"""
        self.tmpdir = tempfile.mkdtemp()
        self.source_base = Path(self.tmpdir) / "data" / "07_model_output"
        self.target_base = Path(self.tmpdir) / "data" / "05_model_input"

    def tearDown(self):
        """一時ディレクトリを削除。"""
        shutil.rmtree(self.tmpdir)

    def test_migration_result_has_migrated_count(self):
        """MigrationResult に migrated カウントが含まれること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.source_base / "cleaned", "b.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.migrated, 2)

    def test_migration_result_has_skipped_count(self):
        """MigrationResult に skipped カウントが含まれること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.target_base / "classified", "a.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.skipped, 1)

    def test_migration_result_has_total(self):
        """MigrationResult の total が migrated + skipped であること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.source_base / "classified", "b.json")
        _create_json_file(self.target_base / "classified", "a.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertEqual(result.total, result.migrated + result.skipped)

    def test_migration_result_has_details_per_subdir(self):
        """MigrationResult に各サブディレクトリの詳細が含まれること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.source_base / "normalized", "b.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
        )
        self.assertIn("classified", result.details)
        self.assertIn("normalized", result.details)
        self.assertEqual(result.details["classified"]["migrated"], 1)
        self.assertEqual(result.details["normalized"]["migrated"], 1)


class TestMigrateDryRun(unittest.TestCase):
    """Dry-run モードテスト (T029)。"""

    def setUp(self):
        """テスト用ディレクトリ構造を作成。"""
        self.tmpdir = tempfile.mkdtemp()
        self.source_base = Path(self.tmpdir) / "data" / "07_model_output"
        self.target_base = Path(self.tmpdir) / "data" / "05_model_input"

    def tearDown(self):
        """一時ディレクトリを削除。"""
        shutil.rmtree(self.tmpdir)

    def test_dry_run_does_not_move_files(self):
        """dry-run モードではファイルが移動されないこと。"""
        source_file = _create_json_file(
            self.source_base / "classified",
            "item.json",
        )
        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
            dry_run=True,
        )
        # Source file should still exist
        self.assertTrue(source_file.exists(), "File should not be moved in dry-run mode")
        # Target file should not exist
        target_file = self.target_base / "classified" / "item.json"
        self.assertFalse(target_file.exists(), "Target should not be created in dry-run mode")

    def test_dry_run_returns_correct_counts(self):
        """dry-run モードでも正しいカウントが返されること。"""
        _create_json_file(self.source_base / "classified", "a.json")
        _create_json_file(self.source_base / "cleaned", "b.json")
        _create_json_file(self.source_base / "normalized", "c.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
            dry_run=True,
        )
        self.assertEqual(result.migrated, 3)
        self.assertEqual(result.skipped, 0)

    def test_dry_run_with_existing_files_counts_skipped(self):
        """dry-run モードでも既存ファイルのスキップカウントが正確であること。"""
        _create_json_file(self.source_base / "classified", "exist.json")
        _create_json_file(self.target_base / "classified", "exist.json")
        _create_json_file(self.source_base / "classified", "new.json")

        result = migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
            dry_run=True,
        )
        self.assertEqual(result.migrated, 1)
        self.assertEqual(result.skipped, 1)

    def test_dry_run_does_not_create_target_dirs(self):
        """dry-run モードでは移行先ディレクトリが作成されないこと。"""
        _create_json_file(self.source_base / "vault_determined", "item.json")
        # Ensure target does not exist
        self.assertFalse(self.target_base.exists())

        migrate_json_to_model_input(
            source_base=self.source_base,
            target_base=self.target_base,
            dry_run=True,
        )
        self.assertFalse(
            (self.target_base / "vault_determined").exists(),
            "Target directory should not be created in dry-run mode",
        )
