"""Tests for Vault Output pipeline nodes (Phase 2 - US1 Preview).

Tests verify:
- Genre to Vault mapping (ai -> engineer Vault)
- Topic subfolder resolution
- Empty topic handling (Vault root placement)
- Topic sanitization (special characters)
- Conflict detection (existing files)
- No-conflict detection
- Preview summary output format
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from obsidian_etl.pipelines.vault_output.nodes import (
    check_conflicts,
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


if __name__ == "__main__":
    unittest.main()
