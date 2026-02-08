"""Tests for BinaryDataset.

Phase 2 RED tests: BinaryDataset load/save/describe unit tests.
These tests verify:
- Loading a ZIP file returns raw bytes
- Saving bytes creates a valid file
- _describe() returns filepath info
- Round-trip: save then load returns same bytes
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from obsidian_etl.datasets import BinaryDataset

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestBinaryDatasetLoad(unittest.TestCase):
    """BinaryDataset: load() returns raw bytes from file."""

    def test_load_zip_file_returns_bytes(self):
        """ZIP ファイルを load すると bytes が返ること。"""
        ds = BinaryDataset(filepath=str(FIXTURES_DIR / "claude_test.zip"))
        data = ds._load()
        self.assertIsInstance(data, bytes)

    def test_load_zip_file_not_empty(self):
        """load した bytes が空でないこと。"""
        ds = BinaryDataset(filepath=str(FIXTURES_DIR / "claude_test.zip"))
        data = ds._load()
        self.assertGreater(len(data), 0)

    def test_load_zip_is_valid_zip(self):
        """load した bytes が有効な ZIP ファイルであること。"""
        ds = BinaryDataset(filepath=str(FIXTURES_DIR / "claude_test.zip"))
        data = ds._load()
        buf = io.BytesIO(data)
        self.assertTrue(zipfile.is_zipfile(buf))

    def test_load_zip_contains_conversations(self):
        """load した ZIP に conversations.json が含まれること。"""
        ds = BinaryDataset(filepath=str(FIXTURES_DIR / "claude_test.zip"))
        data = ds._load()
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf) as zf:
            self.assertIn("conversations.json", zf.namelist())

    def test_load_openai_zip(self):
        """OpenAI テスト ZIP も load できること。"""
        ds = BinaryDataset(filepath=str(FIXTURES_DIR / "openai_test.zip"))
        data = ds._load()
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)


class TestBinaryDatasetSave(unittest.TestCase):
    """BinaryDataset: save() writes raw bytes to file."""

    def test_save_creates_file(self):
        """save すると指定パスにファイルが作成されること。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.zip"
            ds = BinaryDataset(filepath=str(filepath))

            # Create minimal ZIP bytes
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("test.txt", "hello")
            zip_bytes = buf.getvalue()

            ds._save(zip_bytes)
            self.assertTrue(filepath.exists())

    def test_save_creates_parent_dirs(self):
        """save 時に親ディレクトリが自動作成されること。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "dir" / "output.zip"
            ds = BinaryDataset(filepath=str(filepath))
            ds._save(b"test data")
            self.assertTrue(filepath.exists())

    def test_save_then_load_roundtrip(self):
        """save した bytes を load で読み戻すと同一であること。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "roundtrip.zip"
            ds = BinaryDataset(filepath=str(filepath))

            original = b"\x50\x4b\x03\x04test binary data"
            ds._save(original)
            loaded = ds._load()
            self.assertEqual(loaded, original)


class TestBinaryDatasetDescribe(unittest.TestCase):
    """BinaryDataset: _describe() returns metadata dict."""

    def test_describe_returns_dict(self):
        """_describe が dict を返すこと。"""
        ds = BinaryDataset(filepath="/tmp/test.zip")
        desc = ds._describe()
        self.assertIsInstance(desc, dict)

    def test_describe_contains_filepath(self):
        """_describe に filepath が含まれること。"""
        ds = BinaryDataset(filepath="/tmp/test.zip")
        desc = ds._describe()
        self.assertIn("filepath", desc)
        self.assertEqual(desc["filepath"], "/tmp/test.zip")


if __name__ == "__main__":
    unittest.main()
