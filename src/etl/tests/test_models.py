"""Unit tests for core enums and dataclasses.

Tests for:
- Status enums (SessionStatus, PhaseStatus, StageStatus, StepStatus, ItemStatus)
- Type enums (PhaseType, StageType)
- Dataclasses (ProcessingItem, StepResult, RetryConfig)
"""

import unittest
from pathlib import Path

from src.etl.core.models import (
    CHUNK_METADATA_CHUNK_FILENAME,
    CHUNK_METADATA_CHUNK_INDEX,
    CHUNK_METADATA_IS_CHUNKED,
    CHUNK_METADATA_PARENT_ITEM_ID,
    CHUNK_METADATA_TOTAL_CHUNKS,
    ContentMetrics,
    ProcessingItem,
    RetryConfig,
    StageLogRecord,
    StepResult,
    validate_chunk_metadata,
)
from src.etl.core.status import (
    ItemStatus,
    PhaseStatus,
    SessionStatus,
    StageStatus,
    StepStatus,
)
from src.etl.core.types import PhaseType, StageType


class TestSessionStatus(unittest.TestCase):
    """Tests for SessionStatus enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(SessionStatus.PENDING.value, "pending")
        self.assertEqual(SessionStatus.RUNNING.value, "running")
        self.assertEqual(SessionStatus.COMPLETED.value, "completed")
        self.assertEqual(SessionStatus.FAILED.value, "failed")
        self.assertEqual(SessionStatus.PARTIAL.value, "partial")

    def test_member_count(self):
        """Verify exactly 5 members."""
        self.assertEqual(len(SessionStatus), 5)

    def test_from_value(self):
        """Verify enum can be created from string value."""
        self.assertEqual(SessionStatus("pending"), SessionStatus.PENDING)
        self.assertEqual(SessionStatus("completed"), SessionStatus.COMPLETED)


class TestPhaseStatus(unittest.TestCase):
    """Tests for PhaseStatus enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(PhaseStatus.PENDING.value, "pending")
        self.assertEqual(PhaseStatus.RUNNING.value, "running")
        self.assertEqual(PhaseStatus.COMPLETED.value, "completed")
        self.assertEqual(PhaseStatus.FAILED.value, "failed")
        self.assertEqual(PhaseStatus.PARTIAL.value, "partial")

    def test_member_count(self):
        """Verify exactly 5 members."""
        self.assertEqual(len(PhaseStatus), 5)


class TestStageStatus(unittest.TestCase):
    """Tests for StageStatus enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(StageStatus.PENDING.value, "pending")
        self.assertEqual(StageStatus.RUNNING.value, "running")
        self.assertEqual(StageStatus.COMPLETED.value, "completed")
        self.assertEqual(StageStatus.FAILED.value, "failed")

    def test_member_count(self):
        """Verify exactly 4 members (no PARTIAL)."""
        self.assertEqual(len(StageStatus), 4)


class TestStepStatus(unittest.TestCase):
    """Tests for StepStatus enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(StepStatus.PENDING.value, "pending")
        self.assertEqual(StepStatus.RUNNING.value, "running")
        self.assertEqual(StepStatus.COMPLETED.value, "completed")
        self.assertEqual(StepStatus.FAILED.value, "failed")
        self.assertEqual(StepStatus.SKIPPED.value, "skipped")

    def test_member_count(self):
        """Verify exactly 5 members."""
        self.assertEqual(len(StepStatus), 5)


class TestItemStatus(unittest.TestCase):
    """Tests for ItemStatus enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(ItemStatus.PENDING.value, "pending")
        self.assertEqual(ItemStatus.PROCESSING.value, "processing")
        self.assertEqual(ItemStatus.COMPLETED.value, "completed")
        self.assertEqual(ItemStatus.FAILED.value, "failed")
        self.assertEqual(ItemStatus.FILTERED.value, "filtered")

    def test_member_count(self):
        """Verify exactly 5 members."""
        self.assertEqual(len(ItemStatus), 5)


class TestPhaseType(unittest.TestCase):
    """Tests for PhaseType enum."""

    def test_values(self):
        """Verify all expected values exist."""
        self.assertEqual(PhaseType.IMPORT.value, "import")
        self.assertEqual(PhaseType.ORGANIZE.value, "organize")

    def test_member_count(self):
        """Verify exactly 2 members."""
        self.assertEqual(len(PhaseType), 2)


class TestStageType(unittest.TestCase):
    """Tests for StageType enum."""

    def test_values(self):
        """Verify ETL pattern stages."""
        self.assertEqual(StageType.EXTRACT.value, "extract")
        self.assertEqual(StageType.TRANSFORM.value, "transform")
        self.assertEqual(StageType.LOAD.value, "load")

    def test_member_count(self):
        """Verify exactly 3 members (ETL pattern)."""
        self.assertEqual(len(StageType), 3)


class TestProcessingItem(unittest.TestCase):
    """Tests for ProcessingItem dataclass."""

    def test_creation_with_required_fields(self):
        """Verify item can be created with required fields."""
        item = ProcessingItem(
            item_id="test-001",
            source_path=Path("/path/to/file.md"),
            current_step="parse_json",
            status=ItemStatus.PENDING,
            metadata={"key": "value"},
        )

        self.assertEqual(item.item_id, "test-001")
        self.assertEqual(item.source_path, Path("/path/to/file.md"))
        self.assertEqual(item.current_step, "parse_json")
        self.assertEqual(item.status, ItemStatus.PENDING)
        self.assertEqual(item.metadata, {"key": "value"})

    def test_optional_fields_default_to_none(self):
        """Verify optional fields default to None."""
        item = ProcessingItem(
            item_id="test-001",
            source_path=Path("/path/to/file.md"),
            current_step="parse_json",
            status=ItemStatus.PENDING,
            metadata={},
        )

        self.assertIsNone(item.content)
        self.assertIsNone(item.transformed_content)
        self.assertIsNone(item.output_path)
        self.assertIsNone(item.error)

    def test_all_fields(self):
        """Verify all fields can be set."""
        item = ProcessingItem(
            item_id="test-001",
            source_path=Path("/input/file.md"),
            current_step="generate_metadata",
            status=ItemStatus.COMPLETED,
            metadata={"genre": "engineer"},
            content="raw content",
            transformed_content="# Transformed\nContent here",
            output_path=Path("/output/file.md"),
            error=None,
        )

        self.assertEqual(item.content, "raw content")
        self.assertEqual(item.transformed_content, "# Transformed\nContent here")
        self.assertEqual(item.output_path, Path("/output/file.md"))

    def test_mutable_metadata(self):
        """Verify metadata can be modified after creation."""
        item = ProcessingItem(
            item_id="test-001",
            source_path=Path("/path/to/file.md"),
            current_step="parse_json",
            status=ItemStatus.PENDING,
            metadata={"initial": True},
        )

        item.metadata["added"] = "value"
        item.metadata["initial"] = False

        self.assertEqual(item.metadata["added"], "value")
        self.assertFalse(item.metadata["initial"])


class TestStepResult(unittest.TestCase):
    """Tests for StepResult dataclass."""

    def test_success_result(self):
        """Verify successful step result."""
        result = StepResult(
            success=True,
            output={"data": "processed"},
            error=None,
            duration_ms=150,
            items_processed=10,
            items_failed=0,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.output, {"data": "processed"})
        self.assertIsNone(result.error)
        self.assertEqual(result.duration_ms, 150)
        self.assertEqual(result.items_processed, 10)
        self.assertEqual(result.items_failed, 0)

    def test_failed_result(self):
        """Verify failed step result."""
        result = StepResult(
            success=False,
            output=None,
            error="Connection timeout",
            duration_ms=30000,
            items_processed=5,
            items_failed=5,
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.output)
        self.assertEqual(result.error, "Connection timeout")
        self.assertEqual(result.items_failed, 5)

    def test_partial_success(self):
        """Verify partial success (some items failed)."""
        result = StepResult(
            success=True,
            output=["item1", "item2"],
            error=None,
            duration_ms=500,
            items_processed=8,
            items_failed=2,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.items_processed, 8)
        self.assertEqual(result.items_failed, 2)


class TestRetryConfig(unittest.TestCase):
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """Verify default configuration values."""
        config = RetryConfig()

        self.assertEqual(config.max_attempts, 3)
        self.assertEqual(config.min_wait_seconds, 2.0)
        self.assertEqual(config.max_wait_seconds, 30.0)
        self.assertEqual(config.exponential_base, 2.0)
        self.assertTrue(config.jitter)
        self.assertEqual(config.retry_exceptions, (ConnectionError, TimeoutError))

    def test_custom_values(self):
        """Verify custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            min_wait_seconds=1.0,
            max_wait_seconds=60.0,
            exponential_base=3.0,
            jitter=False,
            retry_exceptions=(ValueError, RuntimeError),
        )

        self.assertEqual(config.max_attempts, 5)
        self.assertEqual(config.min_wait_seconds, 1.0)
        self.assertEqual(config.max_wait_seconds, 60.0)
        self.assertEqual(config.exponential_base, 3.0)
        self.assertFalse(config.jitter)
        self.assertEqual(config.retry_exceptions, (ValueError, RuntimeError))

    def test_exception_tuple_is_mutable_default(self):
        """Verify default retry_exceptions is isolated per instance."""
        config1 = RetryConfig()
        config2 = RetryConfig()

        # Default should be equal but not same object (due to field default_factory)
        self.assertEqual(config1.retry_exceptions, config2.retry_exceptions)

    def test_partial_override(self):
        """Verify partial configuration override."""
        config = RetryConfig(max_attempts=10, jitter=False)

        self.assertEqual(config.max_attempts, 10)
        self.assertFalse(config.jitter)
        # Other defaults unchanged
        self.assertEqual(config.min_wait_seconds, 2.0)
        self.assertEqual(config.exponential_base, 2.0)


class TestContentMetrics(unittest.TestCase):
    """Tests for ContentMetrics dataclass."""

    def test_calculate_no_change(self):
        """Verify delta is 0 when sizes are equal."""
        metrics = ContentMetrics.calculate(1000, 1000)

        self.assertEqual(metrics.size_in, 1000)
        self.assertEqual(metrics.size_out, 1000)
        self.assertEqual(metrics.delta, 0.0)
        self.assertEqual(metrics.unit, "bytes")
        self.assertFalse(metrics.review_required)

    def test_calculate_50_percent_reduction(self):
        """Verify delta is -0.5 for 50% reduction."""
        metrics = ContentMetrics.calculate(1000, 500)

        self.assertEqual(metrics.delta, -0.5)
        self.assertTrue(metrics.review_required)

    def test_calculate_double_size(self):
        """Verify delta is 1.0 for doubling (100% increase)."""
        metrics = ContentMetrics.calculate(1000, 2000)

        self.assertEqual(metrics.delta, 1.0)
        self.assertFalse(metrics.review_required)

    def test_calculate_triple_size(self):
        """Verify delta is 2.0 for tripling (200% increase) -> review required."""
        metrics = ContentMetrics.calculate(1000, 3000)

        self.assertEqual(metrics.delta, 2.0)
        self.assertTrue(metrics.review_required)

    def test_calculate_more_than_triple(self):
        """Verify delta > 2.0 triggers review_required."""
        metrics = ContentMetrics.calculate(1000, 5000)

        self.assertEqual(metrics.delta, 4.0)
        self.assertTrue(metrics.review_required)

    def test_calculate_complete_deletion(self):
        """Verify delta is -1.0 for complete deletion (0 output)."""
        metrics = ContentMetrics.calculate(1000, 0)

        self.assertEqual(metrics.delta, -1.0)
        self.assertTrue(metrics.review_required)

    def test_calculate_from_zero_input(self):
        """Verify handling of zero input size."""
        # 0 -> 0 should be -1.0
        metrics = ContentMetrics.calculate(0, 0)
        self.assertEqual(metrics.delta, -1.0)

        # 0 -> N should be N (large value indicating anomaly)
        metrics = ContentMetrics.calculate(0, 100)
        self.assertEqual(metrics.delta, 100.0)
        self.assertTrue(metrics.review_required)

    def test_calculate_custom_unit(self):
        """Verify custom unit is preserved."""
        metrics = ContentMetrics.calculate(100, 200, unit="chars")

        self.assertEqual(metrics.unit, "chars")

    def test_review_required_threshold_boundary(self):
        """Verify exact boundary conditions for review_required."""
        # Just above -0.5 -> no review
        metrics = ContentMetrics.calculate(1000, 501)
        self.assertAlmostEqual(metrics.delta, -0.499, places=2)
        self.assertFalse(metrics.review_required)

        # Exactly -0.5 -> review required
        metrics = ContentMetrics.calculate(1000, 500)
        self.assertEqual(metrics.delta, -0.5)
        self.assertTrue(metrics.review_required)

        # Just below 2.0 -> no review
        metrics = ContentMetrics.calculate(1000, 2999)
        self.assertAlmostEqual(metrics.delta, 1.999, places=2)
        self.assertFalse(metrics.review_required)

        # Exactly 2.0 -> review required
        metrics = ContentMetrics.calculate(1000, 3000)
        self.assertEqual(metrics.delta, 2.0)
        self.assertTrue(metrics.review_required)

    def test_to_dict(self):
        """Verify to_dict serialization."""
        metrics = ContentMetrics.calculate(1000, 500)
        data = metrics.to_dict()

        self.assertEqual(data["size_in"], 1000)
        self.assertEqual(data["size_out"], 500)
        self.assertEqual(data["delta"], -0.5)
        self.assertEqual(data["unit"], "bytes")
        self.assertTrue(data["review_required"])

    def test_direct_construction(self):
        """Verify direct construction with all fields."""
        metrics = ContentMetrics(
            size_in=100,
            size_out=200,
            delta=1.0,
            unit="chars",
        )

        self.assertEqual(metrics.size_in, 100)
        self.assertEqual(metrics.size_out, 200)
        self.assertEqual(metrics.delta, 1.0)
        self.assertEqual(metrics.unit, "chars")
        self.assertFalse(metrics.review_required)


class TestStageLogRecord(unittest.TestCase):
    """Tests for StageLogRecord dataclass."""

    def test_creation_with_required_fields(self):
        """Verify record can be created with required fields only."""
        record = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test.json",
            stage="extract",
            step="parse_json",
            timing_ms=150,
            status="success",
        )

        self.assertEqual(record.timestamp, "2026-01-20T12:00:00Z")
        self.assertEqual(record.session_id, "20260120_120000")
        self.assertEqual(record.filename, "test.json")
        self.assertEqual(record.stage, "extract")
        self.assertEqual(record.step, "parse_json")
        self.assertEqual(record.timing_ms, 150)
        self.assertEqual(record.status, "success")

    def test_optional_fields_default_to_none(self):
        """Verify optional fields default to None."""
        record = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test.json",
            stage="extract",
            step="parse_json",
            timing_ms=150,
            status="success",
        )

        self.assertIsNone(record.file_id)
        self.assertIsNone(record.skipped_reason)
        self.assertIsNone(record.before_chars)
        self.assertIsNone(record.after_chars)
        self.assertIsNone(record.diff_ratio)
        self.assertIsNone(record.is_chunked)
        self.assertIsNone(record.parent_item_id)
        self.assertIsNone(record.chunk_index)

    def test_to_dict_excludes_none_values(self):
        """Verify to_dict excludes None optional fields."""
        record = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test.json",
            stage="extract",
            step="parse_json",
            timing_ms=150,
            status="success",
        )
        data = record.to_dict()

        # Required fields present
        self.assertIn("timestamp", data)
        self.assertIn("session_id", data)
        self.assertIn("filename", data)
        self.assertIn("stage", data)
        self.assertIn("step", data)
        self.assertIn("timing_ms", data)
        self.assertIn("status", data)

        # Optional fields excluded
        self.assertNotIn("file_id", data)
        self.assertNotIn("skipped_reason", data)
        self.assertNotIn("before_chars", data)
        self.assertNotIn("after_chars", data)
        self.assertNotIn("diff_ratio", data)
        self.assertNotIn("is_chunked", data)
        self.assertNotIn("parent_item_id", data)
        self.assertNotIn("chunk_index", data)

    def test_to_dict_includes_chunk_fields_when_set(self):
        """Verify to_dict includes chunk tracking fields when set."""
        record = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test_001.json",
            stage="transform",
            step="extract_knowledge",
            timing_ms=2500,
            status="success",
            file_id="abc123",
            is_chunked=True,
            parent_item_id="parent-uuid",
            chunk_index=0,
        )
        data = record.to_dict()

        self.assertEqual(data["is_chunked"], True)
        self.assertEqual(data["parent_item_id"], "parent-uuid")
        self.assertEqual(data["chunk_index"], 0)
        self.assertEqual(data["file_id"], "abc123")

    def test_non_chunked_record_excludes_chunk_fields(self):
        """Verify non-chunked records exclude chunk fields from to_dict."""
        record = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test.json",
            stage="transform",
            step="extract_knowledge",
            timing_ms=1500,
            status="success",
            file_id="xyz789",
            before_chars=5000,
            after_chars=4800,
            diff_ratio=0.96,
        )
        data = record.to_dict()

        # Standard fields present
        self.assertEqual(data["file_id"], "xyz789")
        self.assertEqual(data["before_chars"], 5000)
        self.assertEqual(data["after_chars"], 4800)
        self.assertEqual(data["diff_ratio"], 0.96)

        # Chunk fields excluded (not set)
        self.assertNotIn("is_chunked", data)
        self.assertNotIn("parent_item_id", data)
        self.assertNotIn("chunk_index", data)

    def test_multiple_chunks_with_different_indices(self):
        """Verify chunk_index can vary for different records."""
        record1 = StageLogRecord(
            timestamp="2026-01-20T12:00:00Z",
            session_id="20260120_120000",
            filename="test_001.json",
            stage="load",
            step="write_file",
            timing_ms=50,
            status="success",
            is_chunked=True,
            parent_item_id="parent-uuid",
            chunk_index=0,
        )

        record2 = StageLogRecord(
            timestamp="2026-01-20T12:00:01Z",
            session_id="20260120_120000",
            filename="test_002.json",
            stage="load",
            step="write_file",
            timing_ms=50,
            status="success",
            is_chunked=True,
            parent_item_id="parent-uuid",
            chunk_index=1,
        )

        data1 = record1.to_dict()
        data2 = record2.to_dict()

        self.assertEqual(data1["chunk_index"], 0)
        self.assertEqual(data2["chunk_index"], 1)
        self.assertEqual(data1["parent_item_id"], data2["parent_item_id"])


class TestChunkMetadataValidation(unittest.TestCase):
    """Tests for chunk metadata validation."""

    def test_non_chunked_item_is_valid(self):
        """Non-chunked items should pass validation."""
        metadata = {"some_field": "value"}
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_non_chunked_explicit_false_is_valid(self):
        """Items with is_chunked=False should pass validation."""
        metadata = {CHUNK_METADATA_IS_CHUNKED: False}
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_chunked_with_all_required_fields_is_valid(self):
        """Chunked items with all required fields should pass validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 0,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_chunked_missing_chunk_index_fails(self):
        """Chunked item missing chunk_index should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("chunk_index is required", error)

    def test_chunked_missing_total_chunks_fails(self):
        """Chunked item missing total_chunks should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 0,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("total_chunks is required", error)

    def test_chunked_missing_parent_item_id_fails(self):
        """Chunked item missing parent_item_id should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 0,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("parent_item_id is required", error)

    def test_chunk_index_negative_fails(self):
        """chunk_index < 0 should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: -1,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("chunk_index must be >= 0", error)

    def test_total_chunks_zero_fails(self):
        """total_chunks = 0 should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 0,
            CHUNK_METADATA_TOTAL_CHUNKS: 0,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("total_chunks must be > 0", error)

    def test_chunk_index_exceeds_total_fails(self):
        """chunk_index >= total_chunks should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 3,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("must be < total_chunks", error)

    def test_chunk_index_boundary_last_valid_index(self):
        """chunk_index = total_chunks - 1 should pass validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 2,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_chunk_filename_is_optional(self):
        """chunk_filename is optional and should not affect validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: 1,
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
            CHUNK_METADATA_CHUNK_FILENAME: "parent_001.json",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_chunk_index_non_integer_fails(self):
        """chunk_index as string should fail validation."""
        metadata = {
            CHUNK_METADATA_IS_CHUNKED: True,
            CHUNK_METADATA_CHUNK_INDEX: "0",
            CHUNK_METADATA_TOTAL_CHUNKS: 3,
            CHUNK_METADATA_PARENT_ITEM_ID: "parent-uuid",
        }
        is_valid, error = validate_chunk_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("chunk_index must be >= 0", error)


if __name__ == "__main__":
    unittest.main()
