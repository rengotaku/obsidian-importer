"""E2E tests for golden file validation.

Phase 3 RED tests: Validate golden files meet quality requirements.

These tests verify:
- FR-006: Golden file set (10-12 files) exists in tests/fixtures/golden/
- FR-007: Files cover conversation types x file sizes matrix
- FR-008: Files include both organized (success) and review (improvement) examples

Success Criteria:
- SC-005: All golden files meet compression threshold
- SC-006: Golden file comparison tests run in CI
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

import yaml

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"
MIN_GOLDEN_FILES = 10
MAX_GOLDEN_FILES = 12


class TestGoldenFilesExist(unittest.TestCase):
    """FR-006: ゴールデンファイルセット（10-12件）が tests/fixtures/golden/ に存在する。"""

    def test_golden_directory_exists(self):
        """tests/fixtures/golden/ ディレクトリが存在すること。"""
        self.assertTrue(
            GOLDEN_DIR.exists(),
            f"Golden directory does not exist: {GOLDEN_DIR}",
        )
        self.assertTrue(
            GOLDEN_DIR.is_dir(),
            f"Golden path is not a directory: {GOLDEN_DIR}",
        )

    def test_readme_exists(self):
        """tests/fixtures/golden/README.md が存在すること。"""
        readme_path = GOLDEN_DIR / "README.md"
        self.assertTrue(
            readme_path.exists(),
            f"README.md does not exist: {readme_path}",
        )

    def test_minimum_golden_files_count(self):
        """ゴールデンファイルが最低10件存在すること（README.md を除く）。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        md_files = list(GOLDEN_DIR.glob("*.md"))
        # Exclude README.md from count
        golden_files = [f for f in md_files if f.name != "README.md"]

        self.assertGreaterEqual(
            len(golden_files),
            MIN_GOLDEN_FILES,
            f"Golden files count {len(golden_files)} is less than minimum {MIN_GOLDEN_FILES}. "
            f"Files found: {[f.name for f in golden_files]}",
        )

    def test_maximum_golden_files_count(self):
        """ゴールデンファイルが最大12件以下であること。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        md_files = list(GOLDEN_DIR.glob("*.md"))
        golden_files = [f for f in md_files if f.name != "README.md"]

        self.assertLessEqual(
            len(golden_files),
            MAX_GOLDEN_FILES,
            f"Golden files count {len(golden_files)} exceeds maximum {MAX_GOLDEN_FILES}. "
            f"Files found: {[f.name for f in golden_files]}",
        )

    def test_all_golden_files_are_markdown(self):
        """全ゴールデンファイルが .md 拡張子であること。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        for f in GOLDEN_DIR.iterdir():
            if f.is_file() and not f.name.startswith("."):
                self.assertEqual(
                    f.suffix,
                    ".md",
                    f"Non-markdown file found in golden directory: {f.name}",
                )


class TestGoldenFilesMeetCompressionThreshold(unittest.TestCase):
    """SC-005: ゴールデンファイルセット全てが圧縮率しきい値を満たす。"""

    def _parse_frontmatter(self, content: str) -> dict | None:
        """Parse YAML frontmatter from Markdown content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            Parsed frontmatter dict or None if parsing fails
        """
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

    def test_golden_files_have_valid_frontmatter(self):
        """全ゴールデンファイルが有効な YAML frontmatter を持つこと。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)
            self.assertIsNotNone(
                frontmatter,
                f"Invalid frontmatter in {golden_file.name}",
            )

    def test_golden_files_have_no_review_reason(self):
        """全ゴールデンファイルに review_reason フィールドがないこと。

        review_reason が存在する = 圧縮率しきい値を満たさなかった
        """
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        failed_files = []
        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)
            if frontmatter and "review_reason" in frontmatter:
                failed_files.append(
                    f"{golden_file.name}: review_reason={frontmatter['review_reason']}"
                )

        self.assertEqual(
            len(failed_files),
            0,
            "Golden files with review_reason (failed compression threshold):\n"
            + "\n".join(failed_files),
        )

    def test_golden_files_have_required_frontmatter_fields(self):
        """全ゴールデンファイルが必須 frontmatter フィールドを持つこと。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        required_fields = {"title", "created", "tags", "file_id", "normalized"}

        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)
            if frontmatter is None:
                self.fail(f"Cannot parse frontmatter in {golden_file.name}")
                continue

            missing_fields = required_fields - set(frontmatter.keys())
            self.assertEqual(
                len(missing_fields),
                0,
                f"Missing required fields in {golden_file.name}: {missing_fields}",
            )


class TestGoldenFilesPreserveTableStructure(unittest.TestCase):
    """FR-003: 表形式データを含むファイルで表形式が保持されること。"""

    def _is_markdown_table(self, line: str) -> bool:
        """Check if a line is part of a Markdown table.

        A Markdown table line starts and ends with |, or contains | with
        dashes for the separator row.
        """
        line = line.strip()
        if not line:
            return False

        # Table row: | col1 | col2 |
        if line.startswith("|") and line.endswith("|"):
            return True

        # Separator row: |---|---|
        if re.match(r"^\|[\s\-:|]+\|$", line):
            return True

        return False

    def _extract_tables(self, content: str) -> list[list[str]]:
        """Extract all Markdown tables from content.

        Returns a list of tables, where each table is a list of lines.
        """
        lines = content.split("\n")
        tables = []
        current_table = []

        for line in lines:
            if self._is_markdown_table(line):
                current_table.append(line)
            else:
                if current_table:
                    # End of table - validate minimum 2 rows (header + separator)
                    if len(current_table) >= 2:
                        tables.append(current_table)
                    current_table = []

        # Don't forget the last table
        if current_table and len(current_table) >= 2:
            tables.append(current_table)

        return tables

    def _validate_table_structure(self, table_lines: list[str]) -> tuple[bool, str]:
        """Validate Markdown table structure.

        Args:
            table_lines: List of table lines

        Returns:
            (is_valid, error_message)
        """
        if len(table_lines) < 2:
            return False, "Table must have at least header and separator rows"

        # Check header row
        header = table_lines[0].strip()
        if not (header.startswith("|") and header.endswith("|")):
            return False, f"Invalid header row: {header}"

        # Check separator row (second row should contain dashes)
        separator = table_lines[1].strip()
        if not re.match(r"^\|[\s\-:|]+\|$", separator):
            return False, f"Invalid separator row: {separator}"

        # Check column count consistency
        header_cols = len(header.split("|")) - 2  # Remove empty first and last
        separator_cols = len(separator.split("|")) - 2

        if header_cols != separator_cols:
            return False, f"Column count mismatch: header={header_cols}, separator={separator_cols}"

        for i, row in enumerate(table_lines[2:], start=2):
            row = row.strip()
            if row.startswith("|") and row.endswith("|"):
                row_cols = len(row.split("|")) - 2
                if row_cols != header_cols:
                    return False, f"Row {i} column count {row_cols} != header {header_cols}"

        return True, ""

    def test_golden_files_with_tables_have_valid_structure(self):
        """表を含むゴールデンファイルで表形式が正しく保持されていること。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        files_with_tables = 0
        invalid_tables = []

        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")

            # Skip frontmatter for table detection
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    body = parts[2]
                else:
                    body = content
            else:
                body = content

            tables = self._extract_tables(body)

            if tables:
                files_with_tables += 1
                for i, table in enumerate(tables):
                    is_valid, error_msg = self._validate_table_structure(table)
                    if not is_valid:
                        invalid_tables.append(f"{golden_file.name} table {i + 1}: {error_msg}")

        # Log info about files with tables
        if files_with_tables == 0:
            self.skipTest("No golden files contain tables")

        self.assertEqual(
            len(invalid_tables),
            0,
            "Invalid table structures found:\n" + "\n".join(invalid_tables),
        )

    def test_at_least_one_golden_file_contains_table(self):
        """少なくとも1つのゴールデンファイルが表を含むこと。

        FR-007: 表形式データを含むファイルがゴールデンセットに含まれる
        """
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        files_with_tables = []
        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")

            # Check if content contains | character (simple table detection)
            if "|" in content:
                # Verify it's actually a table, not just a pipe character
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    body = parts[2] if len(parts) >= 3 else content
                else:
                    body = content

                tables = self._extract_tables(body)
                if tables:
                    files_with_tables.append(golden_file.name)

        self.assertGreater(
            len(files_with_tables),
            0,
            "No golden files contain Markdown tables. "
            "At least one table-containing file is required (FR-007).",
        )


class TestGoldenFilesSelectionMatrix(unittest.TestCase):
    """FR-007/FR-008: ゴールデンファイルが会話タイプ x サイズのマトリクスをカバーする。"""

    def _parse_frontmatter(self, content: str) -> dict | None:
        """Parse YAML frontmatter from Markdown content."""
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

    def _get_file_size_category(self, file_path: Path) -> str:
        """Categorize file by size: small (<2KB), medium (2-5KB), large (>5KB)."""
        size = file_path.stat().st_size
        if size < 2048:
            return "small"
        elif size < 5120:
            return "medium"
        else:
            return "large"

    def _get_content_type(self, frontmatter: dict, body: str) -> str:
        """Determine content type from frontmatter and body.

        Returns: technical, business, daily, table, code, other
        """
        genre = frontmatter.get("genre", "").lower()
        tags = [t.lower() for t in frontmatter.get("tags", [])]

        # Check for table content
        if "|" in body and re.search(r"^\|.*\|$", body, re.MULTILINE):
            return "table"

        # Check for code content
        if "```" in body:
            return "code"

        # Map genre to content type
        if genre == "engineer":
            return "technical"
        elif genre == "business":
            return "business"
        elif genre == "daily":
            return "daily"
        elif genre in ("economy", "other"):
            return "other"

        # Fallback to tag-based detection
        tech_tags = {"python", "javascript", "api", "code", "programming"}
        if any(t in tech_tags for t in tags):
            return "technical"

        return "other"

    def test_golden_files_cover_multiple_genres(self):
        """ゴールデンファイルが複数の genre をカバーすること。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        genres = set()
        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)
            if frontmatter:
                genre = frontmatter.get("genre", "unknown")
                genres.add(genre)

        # Should have at least 2 different genres
        self.assertGreaterEqual(
            len(genres),
            2,
            f"Golden files should cover at least 2 genres. Found: {genres}",
        )

    def test_golden_files_cover_multiple_sizes(self):
        """ゴールデンファイルが複数のサイズカテゴリをカバーすること。"""
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        sizes = set()
        for golden_file in golden_files:
            size_category = self._get_file_size_category(golden_file)
            sizes.add(size_category)

        # Should have at least 2 different size categories
        self.assertGreaterEqual(
            len(sizes),
            2,
            f"Golden files should cover at least 2 size categories. Found: {sizes}",
        )


class TestReviewFolderRatio(unittest.TestCase):
    """SC-002: review フォルダへの振り分け率が 20% 以下になる。

    This test verifies that the golden files meet the compression threshold
    requirements, meaning they would NOT be flagged for review folder.
    Since golden files represent the quality we expect after prompt improvements,
    at least 80% should pass compression validation.
    """

    def _parse_frontmatter(self, content: str) -> dict | None:
        """Parse YAML frontmatter from Markdown content."""
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

    def _get_body_content(self, content: str) -> str:
        """Extract body content (excluding frontmatter).

        Args:
            content: Full Markdown content with YAML frontmatter

        Returns:
            Body content without frontmatter
        """
        if not content.startswith("---"):
            return content
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
        return content

    def test_review_folder_ratio_within_threshold(self):
        """review フォルダへの振り分け率が 20% 以下であること。

        This test validates that the golden files would not be flagged
        for the review folder based on compression ratio validation.
        The test checks:
        1. Files do not have review_reason field (already validated in other tests)
        2. Ratio of files that would fail validation is <= 20%

        User Story 2 Success Criteria:
        - review フォルダへの振り分け率が 20% 以下になる
        """
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        total_files = len(golden_files)
        files_with_review_reason = 0

        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)

            if frontmatter and "review_reason" in frontmatter:
                files_with_review_reason += 1

        # Calculate review folder ratio
        review_ratio = files_with_review_reason / total_files if total_files > 0 else 0

        # SC-002: review folder ratio should be <= 20%
        max_review_ratio = 0.20

        self.assertLessEqual(
            review_ratio,
            max_review_ratio,
            f"Review folder ratio {review_ratio:.1%} exceeds threshold {max_review_ratio:.1%}. "
            f"Files with review_reason: {files_with_review_reason}/{total_files}",
        )

    def test_review_ratio_calculation_details(self):
        """review 振り分け率の詳細を確認するヘルパーテスト。

        This test provides detailed breakdown of:
        - Total golden files
        - Files originally from review/ folder (based on README.md metadata)
        - Files with review_reason field
        - Calculated review ratio
        """
        if not GOLDEN_DIR.exists():
            self.skipTest("Golden directory does not exist")

        golden_files = [f for f in GOLDEN_DIR.glob("*.md") if f.name != "README.md"]

        if len(golden_files) < MIN_GOLDEN_FILES:
            self.skipTest(f"Not enough golden files: {len(golden_files)}")

        # Count files with review_reason
        files_with_review_reason = []
        files_without_review_reason = []

        for golden_file in golden_files:
            content = golden_file.read_text(encoding="utf-8")
            frontmatter = self._parse_frontmatter(content)

            if frontmatter and "review_reason" in frontmatter:
                files_with_review_reason.append(golden_file.name)
            else:
                files_without_review_reason.append(golden_file.name)

        # Assert: All files should NOT have review_reason
        # (Phase 3 removed review_reason from files originally from review/)
        self.assertEqual(
            len(files_with_review_reason),
            0,
            f"Golden files should not have review_reason field after prompt improvements. "
            f"Files with review_reason: {files_with_review_reason}",
        )


if __name__ == "__main__":
    unittest.main()
