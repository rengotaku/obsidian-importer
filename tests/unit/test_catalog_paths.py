"""Tests for catalog.yml dataset path configuration.

Phase 2 RED tests: Verify JSON datasets use 05_model_input/ and MD datasets use 07_model_output/.
These tests validate FR-001, FR-002, FR-003 from spec.md.

Test Strategy:
- Load catalog.yml with PyYAML
- Assert each JSON dataset's `path` starts with `data/05_model_input/`
- Assert each MD dataset's `path` starts with `data/07_model_output/`
- Tests will FAIL (RED) because catalog.yml currently has JSON datasets under 07_model_output/
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

# Project root: 4 levels up from tests/unit/test_catalog_paths.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CATALOG_PATH = _PROJECT_ROOT / "conf" / "base" / "catalog.yml"


def _load_catalog() -> dict:
    """Load catalog.yml and return as dict."""
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestJsonDatasetPaths(unittest.TestCase):
    """JSON datasets must be located under data/05_model_input/."""

    @classmethod
    def setUpClass(cls):
        """Load catalog once for all tests."""
        cls.catalog = _load_catalog()

    def _assert_json_dataset_path(self, dataset_name: str, expected_subdir: str):
        """Assert a JSON dataset path points to 05_model_input/{expected_subdir}."""
        self.assertIn(dataset_name, self.catalog, f"{dataset_name} not found in catalog")
        actual_path = self.catalog[dataset_name]["path"]
        expected_path = f"data/05_model_input/{expected_subdir}"
        self.assertEqual(
            actual_path,
            expected_path,
            f"{dataset_name}: expected path '{expected_path}', got '{actual_path}'",
        )

    def _assert_json_dataset_layer(self, dataset_name: str):
        """Assert a JSON dataset has kedro-viz layer set to model_input."""
        self.assertIn(dataset_name, self.catalog, f"{dataset_name} not found in catalog")
        layer = self.catalog[dataset_name]["metadata"]["kedro-viz"]["layer"]
        self.assertEqual(
            layer,
            "model_input",
            f"{dataset_name}: expected layer 'model_input', got '{layer}'",
        )

    def test_classified_items_path(self):
        """classified_items が data/05_model_input/classified に配置されること。"""
        self._assert_json_dataset_path("classified_items", "classified")

    def test_classified_items_layer(self):
        """classified_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("classified_items")

    def test_existing_classified_items_path(self):
        """existing_classified_items が data/05_model_input/classified に配置されること。"""
        self._assert_json_dataset_path("existing_classified_items", "classified")

    def test_existing_classified_items_layer(self):
        """existing_classified_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("existing_classified_items")

    def test_topic_extracted_items_path(self):
        """topic_extracted_items が data/05_model_input/topic_extracted に配置されること。"""
        self._assert_json_dataset_path("topic_extracted_items", "topic_extracted")

    def test_topic_extracted_items_layer(self):
        """topic_extracted_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("topic_extracted_items")

    def test_normalized_items_path(self):
        """normalized_items が data/05_model_input/normalized に配置されること。"""
        self._assert_json_dataset_path("normalized_items", "normalized")

    def test_normalized_items_layer(self):
        """normalized_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("normalized_items")

    def test_cleaned_items_path(self):
        """cleaned_items が data/05_model_input/cleaned に配置されること。"""
        self._assert_json_dataset_path("cleaned_items", "cleaned")

    def test_cleaned_items_layer(self):
        """cleaned_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("cleaned_items")

    def test_vault_determined_items_path(self):
        """vault_determined_items が data/05_model_input/vault_determined に配置されること。"""
        self._assert_json_dataset_path("vault_determined_items", "vault_determined")

    def test_vault_determined_items_layer(self):
        """vault_determined_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("vault_determined_items")

    def test_organized_items_path(self):
        """organized_items が data/05_model_input/organized に配置されること。"""
        self._assert_json_dataset_path("organized_items", "organized")

    def test_organized_items_layer(self):
        """organized_items の kedro-viz layer が model_input であること。"""
        self._assert_json_dataset_layer("organized_items")


class TestMdDatasetPaths(unittest.TestCase):
    """MD datasets must remain under data/07_model_output/."""

    @classmethod
    def setUpClass(cls):
        """Load catalog once for all tests."""
        cls.catalog = _load_catalog()

    def _assert_md_dataset_path(self, dataset_name: str, expected_subdir: str):
        """Assert an MD dataset path points to 07_model_output/{expected_subdir}."""
        self.assertIn(dataset_name, self.catalog, f"{dataset_name} not found in catalog")
        actual_path = self.catalog[dataset_name]["path"]
        expected_path = f"data/07_model_output/{expected_subdir}"
        self.assertEqual(
            actual_path,
            expected_path,
            f"{dataset_name}: expected path '{expected_path}', got '{actual_path}'",
        )

    def _assert_md_dataset_layer(self, dataset_name: str):
        """Assert an MD dataset has kedro-viz layer set to model_output."""
        self.assertIn(dataset_name, self.catalog, f"{dataset_name} not found in catalog")
        layer = self.catalog[dataset_name]["metadata"]["kedro-viz"]["layer"]
        self.assertEqual(
            layer,
            "model_output",
            f"{dataset_name}: expected layer 'model_output', got '{layer}'",
        )

    def test_markdown_notes_path(self):
        """markdown_notes が data/07_model_output/notes に配置されること。"""
        self._assert_md_dataset_path("markdown_notes", "notes")

    def test_markdown_notes_layer(self):
        """markdown_notes の kedro-viz layer が model_output であること。"""
        self._assert_md_dataset_layer("markdown_notes")

    def test_review_notes_path(self):
        """review_notes が data/07_model_output/review に配置されること。"""
        self._assert_md_dataset_path("review_notes", "review")

    def test_review_notes_layer(self):
        """review_notes の kedro-viz layer が model_output であること。"""
        self._assert_md_dataset_layer("review_notes")

    def test_organized_notes_path(self):
        """organized_notes が data/07_model_output/organized に配置されること。"""
        self._assert_md_dataset_path("organized_notes", "organized")

    def test_organized_notes_layer(self):
        """organized_notes の kedro-viz layer が model_output であること。"""
        self._assert_md_dataset_layer("organized_notes")

    def test_organized_files_path(self):
        """organized_files が data/07_model_output/organized に配置されること。"""
        self._assert_md_dataset_path("organized_files", "organized")

    def test_organized_files_layer(self):
        """organized_files の kedro-viz layer が model_output であること。"""
        self._assert_md_dataset_layer("organized_files")


class TestCatalogDatasetTypes(unittest.TestCase):
    """Verify dataset types are correctly configured after path changes."""

    @classmethod
    def setUpClass(cls):
        """Load catalog once for all tests."""
        cls.catalog = _load_catalog()

    def test_json_datasets_use_json_type(self):
        """JSON datasets (05_model_input) が json.JSONDataset を使用すること。"""
        json_datasets = [
            "classified_items",
            "existing_classified_items",
            "topic_extracted_items",
            "normalized_items",
            "cleaned_items",
            "vault_determined_items",
            "organized_items",
        ]
        for name in json_datasets:
            with self.subTest(dataset=name):
                dataset_type = self.catalog[name]["dataset"]["type"]
                self.assertEqual(
                    dataset_type,
                    "json.JSONDataset",
                    f"{name}: expected 'json.JSONDataset', got '{dataset_type}'",
                )

    def test_md_datasets_use_text_type(self):
        """MD datasets (07_model_output) が text.TextDataset を使用すること。"""
        md_datasets = [
            "markdown_notes",
            "review_notes",
            "organized_notes",
            "organized_files",
        ]
        for name in md_datasets:
            with self.subTest(dataset=name):
                dataset_type = self.catalog[name]["dataset"]["type"]
                self.assertEqual(
                    dataset_type,
                    "text.TextDataset",
                    f"{name}: expected 'text.TextDataset', got '{dataset_type}'",
                )

    def test_no_json_datasets_under_model_output(self):
        """07_model_output 配下に JSON データセットが存在しないこと (FR-001)。"""
        for name, config in self.catalog.items():
            if not isinstance(config, dict) or "path" not in config:
                continue
            path = config["path"]
            if path.startswith("data/07_model_output/"):
                dataset_type = config.get("dataset", {}).get("type", "")
                self.assertNotEqual(
                    dataset_type,
                    "json.JSONDataset",
                    f"{name}: JSON dataset found under 07_model_output/ "
                    f"(path={path}). Should be under 05_model_input/.",
                )
