"""Unit tests for Resume Mode functionality.

Tests for CompletedItemsCache and Resume mode skip logic.

Phase 2: CompletedItemsCache tests (T004-T008)
- test_completed_items_cache_empty
- test_completed_items_cache_with_success
- test_completed_items_cache_ignores_failed
- test_completed_items_cache_stage_filter
- test_completed_items_cache_corrupted_jsonl
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.etl.core.models import CompletedItemsCache
from src.etl.core.types import StageType


class TestCompletedItemsCacheEmpty(unittest.TestCase):
    """T004: Test CompletedItemsCache with empty or non-existent JSONL file."""

    def test_empty_jsonl_returns_empty_cache(self):
        """空の JSONL ファイルから空のキャッシュを返す。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            jsonl_path = Path(f.name)
            # Write nothing - empty file

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 0)
            self.assertEqual(cache.stage, StageType.TRANSFORM)
            self.assertIsInstance(cache.items, set)
        finally:
            jsonl_path.unlink()

    def test_nonexistent_jsonl_returns_empty_cache(self):
        """存在しない JSONL ファイルから空のキャッシュを返す。"""
        nonexistent_path = Path("/tmp/nonexistent_pipeline_stages.jsonl")

        cache = CompletedItemsCache.from_jsonl(nonexistent_path, StageType.TRANSFORM)

        self.assertEqual(len(cache), 0)
        self.assertEqual(cache.stage, StageType.TRANSFORM)

    def test_is_completed_returns_false_for_empty_cache(self):
        """空のキャッシュでは is_completed が常に False を返す。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertFalse(cache.is_completed("any-item-id"))
            self.assertFalse(cache.is_completed(""))
        finally:
            jsonl_path.unlink()


class TestCompletedItemsCacheWithSuccess(unittest.TestCase):
    """T005: Test CompletedItemsCache with successful records."""

    def test_cache_contains_success_items(self):
        """status=success のアイテムがキャッシュに含まれる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write 3 success records
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv1.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "a",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv2.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4500,
                    "status": "success",
                    "item_id": "b",
                },
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv3.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4800,
                    "status": "success",
                    "item_id": "c",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Verify length
            self.assertEqual(len(cache), 3)

            # Verify is_completed returns True for all success items
            self.assertTrue(cache.is_completed("a"))
            self.assertTrue(cache.is_completed("b"))
            self.assertTrue(cache.is_completed("c"))

            # Verify is_completed returns False for unknown items
            self.assertFalse(cache.is_completed("x"))
            self.assertFalse(cache.is_completed("unknown"))
        finally:
            jsonl_path.unlink()

    def test_cache_items_set_contains_correct_ids(self):
        """キャッシュの items セットに正しい item_id が含まれる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "item-001",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4500,
                    "status": "success",
                    "item_id": "item-002",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(cache.items, {"item-001", "item-002"})
        finally:
            jsonl_path.unlink()


class TestCompletedItemsCacheIgnoresFailed(unittest.TestCase):
    """T006: Test CompletedItemsCache ignores failed records."""

    def test_failed_items_not_in_cache(self):
        """status=failed のアイテムはキャッシュに含まれない。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv1.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "a",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv2.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4500,
                    "status": "failed",
                    "item_id": "b",
                    "error_message": "LLM timeout",
                },
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv3.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4800,
                    "status": "success",
                    "item_id": "c",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Verify only success items are in cache
            self.assertEqual(len(cache), 2)
            self.assertTrue(cache.is_completed("a"))
            self.assertFalse(cache.is_completed("b"))  # failed -> not in cache
            self.assertTrue(cache.is_completed("c"))
        finally:
            jsonl_path.unlink()

    def test_mixed_statuses_only_includes_success(self):
        """success/failed/skipped の混在レコードから success のみ抽出。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv1.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "success-1",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv2.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4500,
                    "status": "failed",
                    "item_id": "failed-1",
                },
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv3.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 0,
                    "status": "skipped",
                    "item_id": "skipped-1",
                    "skipped_reason": "duplicate",
                },
                {
                    "timestamp": "2026-01-26T10:00:03+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv4.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4200,
                    "status": "success",
                    "item_id": "success-2",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 2)
            self.assertTrue(cache.is_completed("success-1"))
            self.assertTrue(cache.is_completed("success-2"))
            self.assertFalse(cache.is_completed("failed-1"))
            self.assertFalse(cache.is_completed("skipped-1"))
        finally:
            jsonl_path.unlink()


class TestCompletedItemsCacheStageFilter(unittest.TestCase):
    """T007: Test CompletedItemsCache stage filter."""

    def test_stage_filter_transform_only(self):
        """stage=TRANSFORM のみをフィルタして読み込む。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "a",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "load",
                    "step": "write_file",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "b",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 1)
            self.assertTrue(cache.is_completed("a"))
            self.assertFalse(cache.is_completed("b"))  # load stage -> filtered out
        finally:
            jsonl_path.unlink()

    def test_stage_filter_load_only(self):
        """stage=LOAD のみをフィルタして読み込む。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "transform-item",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "load",
                    "step": "write_file",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "load-item-1",
                },
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "load",
                    "step": "write_file",
                    "timing_ms": 80,
                    "status": "success",
                    "item_id": "load-item-2",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.LOAD)

            self.assertEqual(len(cache), 2)
            self.assertFalse(cache.is_completed("transform-item"))
            self.assertTrue(cache.is_completed("load-item-1"))
            self.assertTrue(cache.is_completed("load-item-2"))
        finally:
            jsonl_path.unlink()

    def test_stage_filter_combined_with_status_filter(self):
        """stage フィルタと status フィルタが両方適用される。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            records = [
                # transform + success -> included
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "t-success",
                },
                # transform + failed -> excluded
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 4500,
                    "status": "failed",
                    "item_id": "t-failed",
                },
                # load + success -> excluded (wrong stage)
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv.json",
                    "stage": "load",
                    "step": "write_file",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "l-success",
                },
            ]
            for record in records:
                f.write(json.dumps(record) + "\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 1)
            self.assertTrue(cache.is_completed("t-success"))
            self.assertFalse(cache.is_completed("t-failed"))
            self.assertFalse(cache.is_completed("l-success"))
        finally:
            jsonl_path.unlink()


class TestCompletedItemsCacheCorruptedJsonl(unittest.TestCase):
    """T008: Test CompletedItemsCache with corrupted JSONL."""

    def test_corrupted_line_skipped_valid_lines_parsed(self):
        """破損した行はスキップされ、有効な行は正しくパースされる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Valid record
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "valid-1",
                    }
                )
                + "\n"
            )
            # Corrupted line (invalid JSON)
            f.write("this is not valid json\n")
            # Another valid record
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:02+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 4800,
                        "status": "success",
                        "item_id": "valid-2",
                    }
                )
                + "\n"
            )
            jsonl_path = Path(f.name)

        try:
            # Should not raise exception, should skip corrupted line
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Valid records should be parsed
            self.assertEqual(len(cache), 2)
            self.assertTrue(cache.is_completed("valid-1"))
            self.assertTrue(cache.is_completed("valid-2"))
        finally:
            jsonl_path.unlink()

    def test_partially_corrupted_json_skipped(self):
        """部分的に壊れた JSON 行はスキップされる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Valid record
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "valid",
                    }
                )
                + "\n"
            )
            # Partial JSON (truncated)
            f.write('{"timestamp": "2026-01-26T10:00:01+00:00", "session_id":\n')
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 1)
            self.assertTrue(cache.is_completed("valid"))
        finally:
            jsonl_path.unlink()

    def test_missing_required_fields_skipped(self):
        """必須フィールドが欠けている行はスキップされる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Valid record
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "complete",
                    }
                )
                + "\n"
            )
            # Record missing item_id
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:01+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        # "item_id" is missing
                    }
                )
                + "\n"
            )
            # Record missing status
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:02+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        # "status" is missing
                        "item_id": "missing-status",
                    }
                )
                + "\n"
            )
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Only the complete record should be in cache
            self.assertEqual(len(cache), 1)
            self.assertTrue(cache.is_completed("complete"))
            self.assertFalse(cache.is_completed("missing-status"))
        finally:
            jsonl_path.unlink()

    def test_empty_lines_skipped(self):
        """空行はスキップされる。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "valid",
                    }
                )
                + "\n"
            )
            f.write("\n")  # Empty line
            f.write("   \n")  # Whitespace-only line
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            self.assertEqual(len(cache), 1)
            self.assertTrue(cache.is_completed("valid"))
        finally:
            jsonl_path.unlink()


# =============================================================================
# Phase 3 Tests: User Story 1 - Skip completed items (T019-T025)
# =============================================================================


class TestSkipCompletedItem(unittest.TestCase):
    """T019: Test that completed items are skipped in Resume mode."""

    def test_skip_completed_item(self):
        """CompletedItemsCache にあるアイテムはスキップされる。

        Given: CompletedItemsCache with item "a" completed
        When: Stage processes items ["a", "b", "c"]
        Then: Only "b" and "c" are processed, "a" is skipped
        """
        # This test requires ResumableStage class which doesn't exist yet
        from src.etl.core.stage import ResumableStage, StageContext

        # Create cache with item "a" completed
        cache = CompletedItemsCache(items={"a"}, stage=StageType.TRANSFORM)

        # Create mock stage context with cache
        ctx = StageContext(
            phase=None,  # Will be mocked
            stage=None,
            debug_mode=False,
            completed_cache=cache,  # NEW: completed_cache field
        )

        # Create mock items
        items = [
            self._create_item("a"),
            self._create_item("b"),
            self._create_item("c"),
        ]

        # Create resumable stage
        stage = ResumableStage()

        # Track which items are actually processed
        processed_ids = []

        def mock_process(item):
            processed_ids.append(item.item_id)
            return item

        stage._process_item = mock_process

        # Run stage
        list(stage.run(ctx, iter(items)))

        # Assert: only "b" and "c" were processed (not "a")
        self.assertEqual(processed_ids, ["b", "c"])
        self.assertNotIn("a", processed_ids)

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestSkipNotLogged(unittest.TestCase):
    """T020: Test that items not in cache are all processed."""

    def test_skip_not_logged(self):
        """空の CompletedItemsCache では全アイテムが処理される。

        Given: Empty CompletedItemsCache
        When: Stage processes items ["a", "b"]
        Then: All items are processed (none skipped)
        """
        from src.etl.core.stage import ResumableStage, StageContext

        # Create empty cache
        cache = CompletedItemsCache(items=set(), stage=StageType.TRANSFORM)

        ctx = StageContext(
            phase=None,
            stage=None,
            debug_mode=False,
            completed_cache=cache,
        )

        items = [
            self._create_item("a"),
            self._create_item("b"),
        ]

        stage = ResumableStage()
        processed_ids = []

        def mock_process(item):
            processed_ids.append(item.item_id)
            return item

        stage._process_item = mock_process

        list(stage.run(ctx, iter(items)))

        # Assert: all items were processed
        self.assertEqual(processed_ids, ["a", "b"])

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestExtractStageSkip(unittest.TestCase):
    """T021: Test that Extract stage is skipped at stage-level."""

    def test_extract_stage_skip(self):
        """Extract 出力フォルダに結果があれば Extract Stage 全体がスキップされる。

        Given: Extract output folder exists with results
        When: Resume mode runs Extract stage
        Then: Entire Extract stage is skipped (stage-level skip)
        """
        from src.etl.phases.import_phase import ImportPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create extract output folder with results
            extract_output = phase_path / "extract" / "output"
            extract_output.mkdir(parents=True)
            (extract_output / "result.json").write_text('{"test": "data"}')

            # Create phase with resume mode
            phase = ImportPhase(base_path=phase_path)

            # Check if extract should be skipped
            should_skip = phase.should_skip_extract_stage()

            self.assertTrue(should_skip)


class TestTransformItemSkip(unittest.TestCase):
    """T022: Test that Transform stage skips completed items.

    Phase 3 Update: run_with_skip() method should be removed.
    Resume logic is now in BaseStage.run() (Phase 2 completed).
    """

    def test_run_with_skip_does_not_exist(self):
        """T031: run_with_skip() メソッドが KnowledgeTransformer に存在しないことを確認。

        Phase 3 - User Story 2: 継承クラスの実装簡素化
        Given: KnowledgeTransformer instance
        When: Check for run_with_skip attribute
        Then: Attribute should NOT exist (Resume logic in BaseStage.run())
        """
        from src.etl.stages.transform.knowledge_transformer import KnowledgeTransformer

        transformer = KnowledgeTransformer()

        # run_with_skip should NOT exist after Phase 3 implementation
        self.assertFalse(
            hasattr(transformer, "run_with_skip"),
            "run_with_skip() should be removed from KnowledgeTransformer. "
            "Resume logic is now in BaseStage.run().",
        )


class TestLoadItemSkip(unittest.TestCase):
    """T023: Test that Load stage skips completed items.

    Phase 3 Update: run_with_skip() method should be removed.
    Resume logic is now in BaseStage.run() (Phase 2 completed).
    """

    def test_run_with_skip_does_not_exist(self):
        """T032: run_with_skip() メソッドが SessionLoader に存在しないことを確認。

        Phase 3 - User Story 2: 継承クラスの実装簡素化
        Given: SessionLoader instance
        When: Check for run_with_skip attribute
        Then: Attribute should NOT exist (Resume logic in BaseStage.run())
        """
        from src.etl.stages.load.session_loader import SessionLoader

        loader = SessionLoader()

        # run_with_skip should NOT exist after Phase 3 implementation
        self.assertFalse(
            hasattr(loader, "run_with_skip"),
            "run_with_skip() should be removed from SessionLoader. "
            "Resume logic is now in BaseStage.run().",
        )


class TestResumePartialCompletion(unittest.TestCase):
    """T024: Test resume with partial completion."""

    def test_resume_partial_completion(self):
        """10件中5件処理済みの場合、5件スキップ・5件処理される。

        Given: 10 items, 5 completed in log
        When: Resume mode runs
        Then: 5 items skipped, 5 items processed
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with 5 success items
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = []
            for i in range(5):
                records.append(
                    {
                        "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                        "session_id": "20260126_100000",
                        "filename": f"item_{i}.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": f"item_{i}",
                    }
                )

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 5)

            # Create 10 items (5 completed, 5 new)
            items = [self._create_item(f"item_{i}") for i in range(10)]

            # Count how many should be skipped vs processed
            skip_count = 0
            process_count = 0
            for item in items:
                if cache.is_completed(item.item_id):
                    skip_count += 1
                else:
                    process_count += 1

            self.assertEqual(skip_count, 5)
            self.assertEqual(process_count, 5)

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestChunkedItemAllSuccessRequired(unittest.TestCase):
    """T024a: Test that all chunks must succeed for chunked item to be skipped."""

    def test_chunked_item_all_success_required(self):
        """3チャンクのうち2チャンクのみ成功の場合、全チャンクが再処理対象。

        Given: 3-chunk item, only 2 chunks succeeded
        When: Resume checks completion
        Then: All 3 chunks marked for reprocessing
        """
        from src.etl.core.models import ChunkedItemsCache

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with 2/3 chunks succeeded
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = [
                # Chunk 0: success
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv_chunk_0.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "conv_chunk_0",
                    "is_chunked": True,
                    "parent_item_id": "conv_original",
                    "chunk_index": 0,
                },
                # Chunk 1: success
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv_chunk_1.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "conv_chunk_1",
                    "is_chunked": True,
                    "parent_item_id": "conv_original",
                    "chunk_index": 1,
                },
                # Chunk 2: failed (not in success list)
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "conv_chunk_2.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "failed",
                    "item_id": "conv_chunk_2",
                    "is_chunked": True,
                    "parent_item_id": "conv_original",
                    "chunk_index": 2,
                    "error_message": "LLM timeout",
                },
            ]

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load chunked items cache (NEW class)
            cache = ChunkedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Check: parent item should NOT be completed (missing chunk 2)
            self.assertFalse(cache.is_parent_completed("conv_original"))

            # All chunks should be marked for reprocessing
            self.assertFalse(cache.is_completed("conv_chunk_0"))
            self.assertFalse(cache.is_completed("conv_chunk_1"))
            self.assertFalse(cache.is_completed("conv_chunk_2"))


class TestChunkedItemPartialFailureRetry(unittest.TestCase):
    """T024b: Test that all chunks succeed means skip all."""

    def test_chunked_item_partial_failure_retry(self):
        """3チャンク全て成功の場合、全チャンクがスキップされる。

        Given: 3-chunk item, all 3 chunks succeeded
        When: Resume checks completion
        Then: All 3 chunks skipped
        """
        from src.etl.core.models import ChunkedItemsCache

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with all 3 chunks succeeded
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": f"conv_chunk_{i}.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": f"conv_chunk_{i}",
                    "is_chunked": True,
                    "parent_item_id": "conv_original",
                    "chunk_index": i,
                }
                for i in range(3)
            ]

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load chunked items cache
            cache = ChunkedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Check: parent item should be completed (all chunks succeeded)
            self.assertTrue(cache.is_parent_completed("conv_original"))

            # All chunks should be skipped
            self.assertTrue(cache.is_completed("conv_chunk_0"))
            self.assertTrue(cache.is_completed("conv_chunk_1"))
            self.assertTrue(cache.is_completed("conv_chunk_2"))


class TestResumeAllCompleted(unittest.TestCase):
    """T025: Test resume when all items are completed."""

    def test_resume_all_completed(self):
        """全アイテム処理済みの場合、全てフィルタされ結果は空。

        Given: All items completed in log
        When: Resume mode runs
        Then: No items yielded, no processing occurs (items are filtered out)

        Phase 2 仕様変更:
        - 処理済みアイテムは yield されない（ステータス変更なし、フィルタのみ）
        - results は空になる
        """
        from src.etl.core.stage import ResumableStage, StageContext

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with all items succeeded
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = [
                {
                    "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                    "session_id": "20260126_100000",
                    "filename": f"item_{i}.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": f"item_{i}",
                }
                for i in range(5)
            ]

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 5)

            # Create stage context with cache
            ctx = StageContext(
                phase=None,
                stage=None,
                debug_mode=False,
                completed_cache=cache,
            )

            # Create resumable stage
            stage = ResumableStage()

            # Track processed items
            processed_ids = []

            def mock_process(item):
                processed_ids.append(item.item_id)
                return item

            stage._process_item = mock_process

            # Create items (all in cache)
            items = [self._create_item(f"item_{i}") for i in range(5)]

            # Run stage
            results = list(stage.run(ctx, iter(items)))

            # Assert: no items were processed
            self.assertEqual(processed_ids, [])

            # Assert: NO items yielded (Phase 2: filter only, no yield)
            # Previously: skipped items were yielded with FILTERED status
            # Now: skipped items are simply not yielded
            self.assertEqual(len(results), 0)

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


# =============================================================================
# Phase 4 Tests: User Story 2 - Retry failed items (T039-T041)
# =============================================================================


class TestRetryFailedItems(unittest.TestCase):
    """T039: Test that all failed items are reprocessed in Resume mode."""

    def test_retry_failed_items(self):
        """pipeline_stages.jsonl に3件の失敗アイテムがある場合、全て再処理される。

        Given: pipeline_stages.jsonl with 3 failed items
        When: Resume mode runs
        Then: All 3 failed items are reprocessed (not skipped)

        FR-008: システムは失敗アイテム（status="failed"）を再処理対象として扱わなければならない
        """
        from src.etl.core.stage import ResumableStage, StageContext

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with 3 failed items
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = [
                {
                    "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                    "session_id": "20260126_100000",
                    "filename": f"failed_{i}.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "failed",
                    "item_id": f"failed_{i}",
                    "error_message": "LLM timeout",
                }
                for i in range(3)
            ]

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache - should be empty (no success items)
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 0)

            # Create stage context with cache
            ctx = StageContext(
                phase=None,
                stage=None,
                debug_mode=False,
                completed_cache=cache,
            )

            # Create resumable stage
            stage = ResumableStage()

            # Track processed items
            processed_ids = []

            def mock_process(item):
                processed_ids.append(item.item_id)
                return item

            stage._process_item = mock_process

            # Create items (all failed in log)
            items = [self._create_item(f"failed_{i}") for i in range(3)]

            # Run stage
            list(stage.run(ctx, iter(items)))

            # Assert: all 3 failed items were reprocessed
            self.assertEqual(len(processed_ids), 3)
            self.assertEqual(set(processed_ids), {"failed_0", "failed_1", "failed_2"})

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestSkipSuccessRetryFailed(unittest.TestCase):
    """T040: Test that success items are skipped while failed items are retried."""

    def test_skip_success_retry_failed(self):
        """3件成功、2件失敗のログ: 成功3件はフィルタされ、失敗2件のみ再処理。

        Given: 3 success items + 2 failed items in log
        When: Resume mode runs
        Then: 2 items processed (failed ones), 3 items filtered out (not yielded)

        Acceptance Scenario from spec.md:
        "Given 3件成功、2件失敗のセッション、When Resume を実行、Then 3件はスキップ、2件は再処理される"

        Phase 2 仕様変更:
        - 処理済み（success）アイテムは yield されない
        - results には処理されたアイテムのみ含まれる（2件）
        """
        from src.etl.core.stage import ResumableStage, StageContext

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with 3 success + 2 failed
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = []

            # 3 success items
            for i in range(3):
                records.append(
                    {
                        "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                        "session_id": "20260126_100000",
                        "filename": f"success_{i}.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": f"success_{i}",
                    }
                )

            # 2 failed items
            for i in range(2):
                records.append(
                    {
                        "timestamp": f"2026-01-26T10:00:{i + 3:02d}+00:00",
                        "session_id": "20260126_100000",
                        "filename": f"failed_{i}.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "failed",
                        "item_id": f"failed_{i}",
                        "error_message": "LLM timeout",
                    }
                )

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache - should only contain success items
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 3)

            # Create stage context with cache
            ctx = StageContext(
                phase=None,
                stage=None,
                debug_mode=False,
                completed_cache=cache,
            )

            # Create resumable stage
            stage = ResumableStage()

            # Track processed items
            processed_ids = []

            def mock_process(item):
                processed_ids.append(item.item_id)
                return item

            stage._process_item = mock_process

            # Create 5 items (3 success in log, 2 failed in log)
            items = [self._create_item(f"success_{i}") for i in range(3)]
            items.extend([self._create_item(f"failed_{i}") for i in range(2)])

            # Run stage
            results = list(stage.run(ctx, iter(items)))

            # Phase 2: Only processed items are yielded (skipped items are filtered out)
            # Assert: 2 items processed (failed), 3 items filtered (not in results)
            self.assertEqual(len(processed_ids), 2)
            self.assertEqual(set(processed_ids), {"failed_0", "failed_1"})

            # Assert: Only 2 results (no skipped items yielded)
            self.assertEqual(len(results), 2)

            # Assert: All results are COMPLETED (processed items only)
            from src.etl.core.status import ItemStatus

            for r in results:
                self.assertEqual(r.status, ItemStatus.COMPLETED)

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestRetrySkippedItems(unittest.TestCase):
    """T041: Test that skipped items are reprocessed in Resume mode."""

    def test_retry_skipped_items(self):
        """status="skipped" のアイテムは Resume 時に再処理される。

        Given: Items with status="skipped" in log
        When: Resume mode runs
        Then: Skipped items are reprocessed (not skipped again)

        FR-009: システムはスキップされたアイテム（status="skipped"）を再処理対象として扱わなければならない

        Note: "skipped" in this context means items that were skipped due to
        business logic (e.g., duplicate detection, MIN_MESSAGES filter).
        These should be retried in case the condition changed.
        """
        from src.etl.core.stage import ResumableStage, StageContext

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Create pipeline_stages.jsonl with 2 skipped items
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = [
                {
                    "timestamp": "2026-01-26T10:00:00+00:00",
                    "session_id": "20260126_100000",
                    "filename": "skipped_0.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 0,
                    "status": "skipped",
                    "item_id": "skipped_0",
                    "skipped_reason": "duplicate",
                },
                {
                    "timestamp": "2026-01-26T10:00:01+00:00",
                    "session_id": "20260126_100000",
                    "filename": "skipped_1.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 0,
                    "status": "skipped",
                    "item_id": "skipped_1",
                    "skipped_reason": "min_messages",
                },
                # Also add 1 success item for comparison
                {
                    "timestamp": "2026-01-26T10:00:02+00:00",
                    "session_id": "20260126_100000",
                    "filename": "success_0.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": "success_0",
                },
            ]

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache - should only contain success items (not skipped)
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 1)  # Only success_0

            # Create stage context with cache
            ctx = StageContext(
                phase=None,
                stage=None,
                debug_mode=False,
                completed_cache=cache,
            )

            # Create resumable stage
            stage = ResumableStage()

            # Track processed items
            processed_ids = []

            def mock_process(item):
                processed_ids.append(item.item_id)
                return item

            stage._process_item = mock_process

            # Create items: 2 skipped + 1 success
            items = [
                self._create_item("skipped_0"),
                self._create_item("skipped_1"),
                self._create_item("success_0"),
            ]

            # Run stage
            list(stage.run(ctx, iter(items)))

            # Assert: skipped items were reprocessed, success item was skipped
            self.assertEqual(len(processed_ids), 2)
            self.assertEqual(set(processed_ids), {"skipped_0", "skipped_1"})
            self.assertNotIn("success_0", processed_ids)

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


# =============================================================================
# Phase 5 Tests: User Story 3 - Crash Recovery (T052-T054)
# =============================================================================


class TestResumeAfterCrash(unittest.TestCase):
    """T052: Test that resume correctly identifies successfully processed items after crash."""

    def test_resume_after_crash_with_incomplete_session(self):
        """クラッシュ後の Resume で、成功済みアイテムが正しく識別される。

        Given: Session crashed after processing 5 of 10 items
               pipeline_stages.jsonl contains 5 success records
               (crash occurred mid-processing, no partial write)
        When: Resume mode starts
        Then: 5 completed items are skipped, 5 remaining items are processed

        FR-010 (SC-004): Crash recovery should have at most 1 duplicate processed item
        """
        from src.etl.core.stage import ResumableStage, StageContext

        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)

            # Simulate crash scenario:
            # 10 items total, 5 successfully processed before crash
            jsonl_path = phase_path / "pipeline_stages.jsonl"
            records = []

            # First 5 items completed successfully
            for i in range(5):
                records.append(
                    {
                        "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                        "session_id": "20260126_100000",
                        "filename": f"item_{i}.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": f"item_{i}",
                    }
                )

            with open(jsonl_path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            # Load cache - should contain 5 completed items
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)
            self.assertEqual(len(cache), 5)

            # Create stage context
            ctx = StageContext(
                phase=None,
                stage=None,
                debug_mode=False,
                completed_cache=cache,
            )

            # Create resumable stage
            stage = ResumableStage()

            # Track processed items
            processed_ids = []

            def mock_process(item):
                processed_ids.append(item.item_id)
                return item

            stage._process_item = mock_process

            # Create 10 items (5 completed, 5 new - simulating resume after crash)
            items = [self._create_item(f"item_{i}") for i in range(10)]

            # Run stage with resume
            results = list(stage.run(ctx, iter(items)))

            # Assert: Only items 5-9 were processed (items 0-4 skipped)
            self.assertEqual(len(processed_ids), 5)
            self.assertEqual(
                set(processed_ids),
                {"item_5", "item_6", "item_7", "item_8", "item_9"},
            )

            # Assert: Items 0-4 were NOT processed (skipped)
            for i in range(5):
                self.assertNotIn(f"item_{i}", processed_ids)

    def test_resume_after_crash_preserves_previous_success(self):
        """クラッシュ後の再実行で、以前の成功結果が保持される。

        Given: First run: 3 success, then crash
               Resume run: 2 more success
        When: Check final state
        Then: Total 5 success items tracked

        This verifies that resume mode preserves previous success records.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            phase_path = Path(tmpdir)
            jsonl_path = phase_path / "pipeline_stages.jsonl"

            # First run: 3 items succeeded before crash
            first_run_records = [
                {
                    "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                    "session_id": "20260126_100000",
                    "filename": f"item_{i}.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": f"item_{i}",
                }
                for i in range(3)
            ]

            with open(jsonl_path, "w") as f:
                for record in first_run_records:
                    f.write(json.dumps(record) + "\n")

            # Simulate resume: Add 2 more success records (appended after resume)
            resume_records = [
                {
                    "timestamp": f"2026-01-26T11:00:{i:02d}+00:00",
                    "session_id": "20260126_100000",
                    "filename": f"item_{i + 3}.json",
                    "stage": "transform",
                    "step": "extract_knowledge",
                    "timing_ms": 5000,
                    "status": "success",
                    "item_id": f"item_{i + 3}",
                }
                for i in range(2)
            ]

            with open(jsonl_path, "a") as f:  # Append mode
                for record in resume_records:
                    f.write(json.dumps(record) + "\n")

            # Load cache - should contain all 5 items
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: All 5 items from both runs are in cache
            self.assertEqual(len(cache), 5)
            for i in range(5):
                self.assertTrue(cache.is_completed(f"item_{i}"))

    def _create_item(self, item_id: str):
        """Helper to create mock ProcessingItem."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus

        return ProcessingItem(
            item_id=item_id,
            source_path=Path(f"/tmp/{item_id}.json"),
            current_step="test",
            status=ItemStatus.PENDING,
            metadata={},
            content=f"content for {item_id}",
        )


class TestCorruptedLogRecovery(unittest.TestCase):
    """T053: Test that CompletedItemsCache handles corrupted JSONL gracefully.

    This extends T008 tests with more crash-specific scenarios.
    """

    def test_corrupted_log_recovery_with_warning(self):
        """破損した JSONL 行は警告付きでスキップされ、有効な行は処理される。

        Given: JSONL with mix of valid and corrupted records
        When: CompletedItemsCache.from_jsonl() is called
        Then: Valid records are parsed, corrupted ones are skipped with warning

        FR-014: System must skip corrupted log records with warning
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Valid record 1
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv1.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "valid-1",
                    }
                )
                + "\n"
            )
            # Corrupted: Invalid JSON (garbage text)
            f.write("not valid json at all\n")
            # Corrupted: JSON but wrong format (array instead of object)
            f.write("[1, 2, 3]\n")
            # Valid record 2
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:02+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv2.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 4800,
                        "status": "success",
                        "item_id": "valid-2",
                    }
                )
                + "\n"
            )
            # Corrupted: Missing closing brace (truncated)
            f.write('{"timestamp": "2026-01-26T10:00:03+00:00", "session_id"\n')
            # Valid record 3
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:04+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv3.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 4600,
                        "status": "success",
                        "item_id": "valid-3",
                    }
                )
                + "\n"
            )
            jsonl_path = Path(f.name)

        try:
            # Should parse without exception
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: Only valid records are in cache
            self.assertEqual(len(cache), 3)
            self.assertTrue(cache.is_completed("valid-1"))
            self.assertTrue(cache.is_completed("valid-2"))
            self.assertTrue(cache.is_completed("valid-3"))

            # Corrupted records should not be present
            # (we can't directly verify warnings without mocking logging)
        finally:
            jsonl_path.unlink()

    def test_corrupted_log_recovery_all_corrupted(self):
        """全ての行が破損している場合、空のキャッシュが返される。

        Given: JSONL with all corrupted records
        When: CompletedItemsCache.from_jsonl() is called
        Then: Empty cache is returned (no exception thrown)
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # All corrupted lines
            f.write("not valid json\n")
            f.write('{"incomplete": true\n')
            f.write("[1, 2, 3]\n")
            f.write("another garbage line\n")
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: Empty cache (no valid records)
            self.assertEqual(len(cache), 0)
        finally:
            jsonl_path.unlink()

    def test_corrupted_log_recovery_unicode_issues(self):
        """Unicode エンコーディング問題がある行もスキップされる。

        Given: JSONL with some lines having encoding issues
        When: CompletedItemsCache.from_jsonl() is called
        Then: Valid records are parsed, problematic ones are handled gracefully
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            # Valid record with unicode
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:00+00:00",
                        "session_id": "20260126_100000",
                        "filename": "unicode_日本語.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": "unicode-item",
                    }
                )
                + "\n"
            )
            # Line with control characters (can cause JSON parse issues)
            f.write('{"bad": "line with \\x00 null"}\n')
            # Valid record
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-01-26T10:00:01+00:00",
                        "session_id": "20260126_100000",
                        "filename": "conv.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 4800,
                        "status": "success",
                        "item_id": "valid-item",
                    }
                )
                + "\n"
            )
            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: Valid records are in cache
            self.assertTrue(cache.is_completed("unicode-item"))
            self.assertTrue(cache.is_completed("valid-item"))
        finally:
            jsonl_path.unlink()


class TestPartialLogRecovery(unittest.TestCase):
    """T054: Test recovery from partial JSONL write (crash mid-write)."""

    def test_partial_log_last_line_truncated(self):
        """最終行が途中で切れている場合（クラッシュ時の部分書き込み）。

        Given: JSONL where last line is truncated (crash during write)
        When: CompletedItemsCache.from_jsonl() is called
        Then: Complete records are parsed, truncated last line is skipped

        Scenario: 100件中50件処理時にクラッシュ、最後の行が途中で切れている
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # 49 complete records
            for i in range(49):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T10:00:{i % 60:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"item_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "success",
                            "item_id": f"item_{i}",
                        }
                    )
                    + "\n"
                )

            # Last line truncated (simulating crash during write)
            # This is what happens when the process is killed mid-write
            f.write(
                '{"timestamp": "2026-01-26T10:00:49+00:00", "session_id": "20260126_100000", "filename": "item_49.json", "stage": "trans'
            )
            # No newline, no closing brace - truncated mid-write

            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: 49 complete records are in cache
            self.assertEqual(len(cache), 49)

            # Verify first and last complete records
            self.assertTrue(cache.is_completed("item_0"))
            self.assertTrue(cache.is_completed("item_48"))

            # Truncated record should NOT be present
            self.assertFalse(cache.is_completed("item_49"))
        finally:
            jsonl_path.unlink()

    def test_partial_log_empty_last_line(self):
        """最終行が空（改行のみ）の場合。

        Given: JSONL with trailing newlines
        When: CompletedItemsCache.from_jsonl() is called
        Then: All valid records are parsed, empty lines are ignored
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Complete records
            for i in range(5):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"item_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "success",
                            "item_id": f"item_{i}",
                        }
                    )
                    + "\n"
                )

            # Trailing empty lines (common after crash recovery attempts)
            f.write("\n")
            f.write("\n")
            f.write("   \n")  # Whitespace-only line

            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: All 5 complete records are in cache
            self.assertEqual(len(cache), 5)
            for i in range(5):
                self.assertTrue(cache.is_completed(f"item_{i}"))
        finally:
            jsonl_path.unlink()

    def test_partial_log_multiple_crash_recoveries(self):
        """複数回のクラッシュと復旧を経たログファイル。

        Given: JSONL with multiple truncated lines from repeated crashes
        When: CompletedItemsCache.from_jsonl() is called
        Then: All complete records are parsed, all truncated lines are skipped

        Scenario: Multiple crash/resume cycles resulted in a messy log file
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # First run: 2 complete records
            for i in range(2):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"run1_item_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "success",
                            "item_id": f"run1_item_{i}",
                        }
                    )
                    + "\n"
                )

            # First crash: truncated line
            f.write('{"timestamp": "crash1", "session_id":')

            # Resume adds newline before continuing (some implementations do this)
            f.write("\n")

            # Second run: 3 more complete records
            for i in range(3):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T11:00:{i:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"run2_item_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "success",
                            "item_id": f"run2_item_{i}",
                        }
                    )
                    + "\n"
                )

            # Second crash: another truncated line
            f.write('{"timestamp": "crash2"')

            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: 5 complete records are in cache (2 from run1 + 3 from run2)
            self.assertEqual(len(cache), 5)

            # Verify run1 items
            self.assertTrue(cache.is_completed("run1_item_0"))
            self.assertTrue(cache.is_completed("run1_item_1"))

            # Verify run2 items
            self.assertTrue(cache.is_completed("run2_item_0"))
            self.assertTrue(cache.is_completed("run2_item_1"))
            self.assertTrue(cache.is_completed("run2_item_2"))
        finally:
            jsonl_path.unlink()

    def test_partial_log_with_failed_items_after_crash(self):
        """クラッシュ後の Resume で、以前の失敗アイテムも再処理される。

        Given: Log with both success and failed records, then crash
        When: Resume loads cache
        Then: Only success items are in cache, failed items will be reprocessed

        This combines crash recovery with retry logic.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Success records
            for i in range(3):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T10:00:{i:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"success_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "success",
                            "item_id": f"success_{i}",
                        }
                    )
                    + "\n"
                )

            # Failed records
            for i in range(2):
                f.write(
                    json.dumps(
                        {
                            "timestamp": f"2026-01-26T10:00:{i + 3:02d}+00:00",
                            "session_id": "20260126_100000",
                            "filename": f"failed_{i}.json",
                            "stage": "transform",
                            "step": "extract_knowledge",
                            "timing_ms": 5000,
                            "status": "failed",
                            "item_id": f"failed_{i}",
                            "error_message": "LLM timeout",
                        }
                    )
                    + "\n"
                )

            # Truncated line (crash)
            f.write('{"timestamp": "crash",')

            jsonl_path = Path(f.name)

        try:
            cache = CompletedItemsCache.from_jsonl(jsonl_path, StageType.TRANSFORM)

            # Assert: Only 3 success items are in cache
            self.assertEqual(len(cache), 3)

            # Success items should be in cache
            for i in range(3):
                self.assertTrue(cache.is_completed(f"success_{i}"))

            # Failed items should NOT be in cache (will be retried)
            for i in range(2):
                self.assertFalse(cache.is_completed(f"failed_{i}"))
        finally:
            jsonl_path.unlink()


# =============================================================================
# Phase 5 Tests: User Story 1 - Resume モードでの Extract 重複ログ防止 (T055-T059)
# =============================================================================


class TestResumeModeExtractReuse(unittest.TestCase):
    """T055-T059: Test Resume mode Extract output reuse.

    User Story 1 - Resume モードでの Extract 重複ログ防止 (Priority: P1)

    ETL パイプラインを Resume モードで再実行する際、Extract stage の output が既に存在する場合は、
    input フォルダから再処理せずに output の JSONL ファイルから ProcessingItem を復元する。
    これにより、pipeline_stages.jsonl への Extract ログの重複記録を防止する。
    """

    def test_resume_mode_loads_from_extract_output(self):
        """T056: Resume mode loads ProcessingItem from extract/output/*.jsonl.

        Acceptance Scenario 1:
        Given Extract stage の output フォルダに data-dump-*.jsonl が存在する状態で,
        When Resume モードで import コマンドを実行した場合,
        Then Extract stage は input フォルダを処理せず、output の JSONL から ProcessingItem を復元する

        FR-002: BasePhaseOrchestrator.run() は Extract output（data-dump-*.jsonl）の存在を確認し、
        存在する場合は JSONL から ProcessingItem を復元する
        """
        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        # Track if extract stage was called
        extract_stage_called = [False]

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                extract_stage_called[0] = True
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = TestOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_100000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Create extract output with data-dump file (simulate previous run)
            extract_output = phase.base_path / "extract" / "output"
            item_data = {
                "item_id": "previous-run-item",
                "source_path": "/test/conv.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "previous content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Run orchestrator (should Resume from extract output)
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: Extract stage was NOT called (loaded from output instead)
            self.assertFalse(
                extract_stage_called[0],
                "Extract stage should NOT be called when extract/output/*.jsonl exists (Resume mode)",
            )

    def test_resume_mode_no_extract_log_appended(self):
        """T057: No Extract log appended to pipeline_stages.jsonl in Resume mode.

        Acceptance Scenario 2:
        Given Resume モードで Extract output から復元した場合,
        When pipeline_stages.jsonl を確認すると,
        Then 新しい Extract ログは追記されていない

        FR-008: Resume モードで Extract output から復元した場合、
        pipeline_stages.jsonl に新しい Extract ログは追記されない

        SC-001: Resume モードで Extract stage を再実行した際、
        pipeline_stages.jsonl への Extract ログ追記が 0 件である
        """
        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        # Counter for pipeline_stages writes
        pipeline_writes = {"extract": 0}

        class LogTrackingOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                # This should NOT be called in Resume mode
                pipeline_writes["extract"] += 1
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = LogTrackingOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_110000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Create existing pipeline_stages.jsonl (simulating previous run)
            pipeline_stages_path = phase.base_path / "pipeline_stages.jsonl"
            existing_records = [
                {
                    "timestamp": "2026-01-29T09:00:00+00:00",
                    "session_id": "20260129_090000",
                    "filename": "conv.json",
                    "stage": "extract",
                    "step": "parse",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "previous-item",
                },
            ]
            with open(pipeline_stages_path, "w") as f:
                for record in existing_records:
                    f.write(json.dumps(record) + "\n")

            # Create extract output with data-dump file (Resume mode trigger)
            extract_output = phase.base_path / "extract" / "output"
            item_data = {
                "item_id": "previous-run-item",
                "source_path": "/test/conv.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "previous content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Run orchestrator in Resume mode
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: Extract stage was NOT called (no new Extract logs)
            self.assertEqual(
                pipeline_writes["extract"],
                0,
                "No Extract stage calls should occur in Resume mode (no new Extract logs)",
            )

    def test_resume_mode_stdout_message(self):
        """T058: Standard output message "Resume mode: Loading from extract/output/*.jsonl".

        Acceptance Scenario (US2, Scenario 3):
        Given Resume モードで実行中,
        When Extract output から復元した場合,
        Then 標準出力に「Resume mode: Loading from extract/output/*.jsonl」と表示される

        FR-002: FW が Resume モード検出時にメッセージを出力する
        """
        import logging

        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = TestOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Create extract output with data-dump file (Resume mode trigger)
            extract_output = phase.base_path / "extract" / "output"
            item_data = {
                "item_id": "test-item",
                "source_path": "/test/conv.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "test content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Capture log output
            with self.assertLogs("src.etl.core.phase_orchestrator", level=logging.INFO) as cm:
                orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: Resume mode message was logged
            resume_message_found = any(
                "Resume mode: Loading from extract/output/*.jsonl" in msg for msg in cm.output
            )
            self.assertTrue(
                resume_message_found,
                f"Expected 'Resume mode: Loading from extract/output/*.jsonl' in logs, got: {cm.output}",
            )

    def test_extract_output_not_found_message(self):
        """T059: "Extract output not found, processing from input/" when output is empty.

        Acceptance Scenario 3 (US1):
        Given Extract stage の output フォルダが空の状態で,
        When Resume モードで import コマンドを実行した場合,
        Then 標準出力に「Extract output not found, processing from input/」と表示され、
        通常通り input フォルダから処理される

        FR-003: BasePhaseOrchestrator.run() は Extract output が存在しない場合、
        標準出力にメッセージを表示し、input フォルダから通常処理を行う
        """
        import logging

        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        # Track if extract stage was called
        extract_stage_called = [False]

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                extract_stage_called[0] = True
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = TestOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_130000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders (but NO data-dump files in extract/output)
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Capture log output
            with self.assertLogs("src.etl.core.phase_orchestrator", level=logging.INFO) as cm:
                orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: "Extract output not found" message was logged
            not_found_message_found = any(
                "Extract output not found, processing from input/" in msg for msg in cm.output
            )
            self.assertTrue(
                not_found_message_found,
                f"Expected 'Extract output not found, processing from input/' in logs, got: {cm.output}",
            )

            # Assert: Extract stage WAS called (normal processing)
            self.assertTrue(
                extract_stage_called[0],
                "Extract stage should be called when no extract output exists (normal mode)",
            )


class TestImportPhaseResumeModeExtractReuse(unittest.TestCase):
    """T055-T059: Test ImportPhase.run() Resume mode Extract output reuse.

    User Story 1 - Resume モードでの Extract 重複ログ防止 (Priority: P1)

    Phase 5 では ImportPhase.run() が BasePhaseOrchestrator の Resume ロジックを
    正しく使用することを検証する。現在 ImportPhase.run() は独自の run() を持っており、
    BasePhaseOrchestrator.run() の Resume ロジックを使用していない。

    これらのテストは現在の実装では FAIL する（RED フェーズ）。
    """

    def test_import_phase_run_skips_extract_when_output_exists(self):
        """T056-A: ImportPhase.run() skips Extract stage when extract/output/*.jsonl exists.

        Acceptance Scenario 1:
        Given Extract stage の output フォルダに data-dump-*.jsonl が存在する状態で,
        When ImportPhase.run() を実行した場合,
        Then Extract stage は input フォルダを処理せず、output の JSONL から ProcessingItem を復元する

        NOTE: 現在の ImportPhase.run() は独自ロジックで常に Extract を実行するため、
        このテストは FAIL する。GREEN フェーズで修正が必要。
        """
        from unittest.mock import MagicMock, patch

        from src.etl.core.phase import Phase
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType
        from src.etl.phases.import_phase import ImportPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_160000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders and data structures
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()
                phase.stages[stage_type] = stage

            # Create extract input (source files that would be processed normally)
            extract_input = phase.base_path / "extract" / "input"
            input_file = extract_input / "conversations.json"
            input_file.write_text(
                json.dumps(
                    [
                        {
                            "uuid": "new-conversation-uuid",
                            "name": "New Conversation",
                            "chat_messages": [
                                {"sender": "human", "text": "Hello"},
                                {"sender": "assistant", "text": "Hi there!"},
                                {"sender": "human", "text": "Test"},
                            ],
                        }
                    ]
                )
            )

            # Create extract output with data-dump file (simulate previous run's output)
            extract_output = phase.base_path / "extract" / "output"
            item_data = {
                "item_id": "previous-run-item-uuid",
                "source_path": str(input_file),
                "current_step": "extract",
                "status": "completed",
                "metadata": {"conversation_uuid": "previous-run-item-uuid"},
                "content": "previous content that should be used in Resume mode",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Count extract stage logs BEFORE running
            pipeline_stages_path = phase.base_path / "pipeline_stages.jsonl"
            extract_logs_before = 0

            # Create ImportPhase (NOT in Resume mode via base_path)
            import_phase = ImportPhase(provider="claude")

            # Mock Extract stage to track if it's called
            extract_called = [False]

            def mock_discover_items(self, input_path, chunk=False):
                """Track if discover_items is called (meaning Extract is running).

                Note: This is an instance method, so 'self' is the first parameter.
                """
                extract_called[0] = True
                # Return empty to avoid actual processing
                return iter([])

            # Patch discover_items on ClaudeExtractor
            from src.etl.stages.extract.claude_extractor import ClaudeExtractor

            with patch.object(ClaudeExtractor, "discover_items", mock_discover_items):
                try:
                    import_phase.run(phase_data=phase, debug_mode=False)
                except Exception:
                    pass  # May fail for other reasons

            # Assert: Extract stage should NOT be called when extract/output/*.jsonl exists
            # This will FAIL with current implementation because ImportPhase.run() always runs Extract
            self.assertFalse(
                extract_called[0],
                "ImportPhase.run() should skip Extract stage when extract/output/*.jsonl exists. "
                "Current implementation always runs Extract regardless of existing output. "
                "Phase 5 GREEN should fix this.",
            )

    def test_import_phase_run_no_new_extract_logs_in_resume_mode(self):
        """T057-A: ImportPhase.run() does not append Extract logs when resuming.

        Acceptance Scenario 2:
        Given Extract stage の output フォルダに data-dump-*.jsonl が存在し、
              pipeline_stages.jsonl に既存の Extract ログが N 件ある状態で,
        When ImportPhase.run() を実行した場合,
        Then pipeline_stages.jsonl の Extract ログ件数は N のまま変わらない

        SC-001: Resume モードで Extract stage を再実行した際、
        pipeline_stages.jsonl への Extract ログ追記が 0 件である
        """
        from src.etl.core.phase import Phase
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType
        from src.etl.phases.import_phase import ImportPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_170000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders and data structures
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()
                phase.stages[stage_type] = stage

            # Create existing pipeline_stages.jsonl with 2 Extract logs
            pipeline_stages_path = phase.base_path / "pipeline_stages.jsonl"
            existing_records = [
                {
                    "timestamp": "2026-01-29T09:00:00+00:00",
                    "session_id": "20260129_090000",
                    "filename": "conv1.json",
                    "stage": "extract",
                    "step": "parse",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "previous-item-1",
                },
                {
                    "timestamp": "2026-01-29T09:00:01+00:00",
                    "session_id": "20260129_090000",
                    "filename": "conv2.json",
                    "stage": "extract",
                    "step": "parse",
                    "timing_ms": 100,
                    "status": "success",
                    "item_id": "previous-item-2",
                },
            ]
            with open(pipeline_stages_path, "w") as f:
                for record in existing_records:
                    f.write(json.dumps(record) + "\n")

            extract_logs_before = 2

            # Create extract input (with actual conversations that would be processed)
            extract_input = phase.base_path / "extract" / "input"
            input_file = extract_input / "conversations.json"
            input_file.write_text(
                json.dumps(
                    [
                        {
                            "uuid": "new-conversation-uuid",
                            "name": "New Conversation",
                            "chat_messages": [
                                {"sender": "human", "text": "Hello"},
                                {"sender": "assistant", "text": "Hi there!"},
                                {"sender": "human", "text": "Test"},
                            ],
                        }
                    ]
                )
            )

            # Create extract output with data-dump file (Resume mode trigger)
            extract_output = phase.base_path / "extract" / "output"
            item_data = {
                "item_id": "previous-item-1",
                "source_path": str(input_file),
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "previous content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Create ImportPhase
            import_phase = ImportPhase(provider="claude")

            try:
                import_phase.run(phase_data=phase, debug_mode=False)
            except Exception:
                pass  # May fail for other reasons

            # Count Extract logs AFTER running
            extract_logs_after = 0
            if pipeline_stages_path.exists():
                with open(pipeline_stages_path, encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                            if record.get("stage") == "extract":
                                extract_logs_after += 1
                        except json.JSONDecodeError:
                            continue

            # Assert: No new Extract logs should be added
            # This will FAIL with current implementation because ImportPhase.run() always runs Extract
            self.assertEqual(
                extract_logs_after,
                extract_logs_before,
                f"ImportPhase.run() should NOT add Extract logs when extract/output/*.jsonl exists. "
                f"Expected {extract_logs_before} Extract logs, got {extract_logs_after}. "
                f"Phase 5 GREEN should fix this.",
            )


class TestResumeModeExtractLogIntegration(unittest.TestCase):
    """Integration tests for Resume mode Extract log prevention.

    Tests the full pipeline behavior to ensure Extract logs are not duplicated.
    """

    def test_resume_mode_preserves_extract_output_items(self):
        """Resume mode correctly restores all items from extract output.

        Given: extract/output/ に 3 個の ProcessingItem が data-dump-0001.jsonl に保存されている
        When: Resume モードで run() を呼び出した場合
        Then: 3 個の ProcessingItem がすべて復元され、Transform/Load stage に渡される
        """
        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        # Track items received by transform stage
        items_received_by_transform = []

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                return items

            def _run_transform_stage(self, ctx, items):
                items_list = list(items)
                items_received_by_transform.extend(items_list)
                return iter(items_list)

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = TestOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_140000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Create extract output with 3 items
            extract_output = phase.base_path / "extract" / "output"
            items_data = []
            for i in range(3):
                item_data = {
                    "item_id": f"item-{i:03d}",
                    "source_path": f"/test/conv{i}.json",
                    "current_step": "extract",
                    "status": "completed",
                    "metadata": {"index": i},
                    "content": f"content {i}",
                    "transformed_content": None,
                    "output_path": None,
                    "error": None,
                }
                items_data.append(item_data)

            data_dump_file = extract_output / "data-dump-0001.jsonl"
            with open(data_dump_file, "w") as f:
                for item in items_data:
                    f.write(json.dumps(item) + "\n")

            # Run orchestrator in Resume mode
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: All 3 items were restored and passed to transform
            self.assertEqual(len(items_received_by_transform), 3)

            item_ids = {item.item_id for item in items_received_by_transform}
            self.assertEqual(item_ids, {"item-000", "item-001", "item-002"})

    def test_resume_mode_with_multiple_data_dump_files(self):
        """Resume mode correctly loads from multiple data-dump-*.jsonl files.

        Given: extract/output/ に data-dump-0001.jsonl (2 items) と data-dump-0002.jsonl (1 item)
        When: Resume モードで run() を呼び出した場合
        Then: 3 個の ProcessingItem がすべて復元される（ファイル順で読み込み）
        """
        from src.etl.core.phase import Phase
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.core.stage import Stage
        from src.etl.core.types import PhaseType, StageType

        items_received = []

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                return items

            def _run_transform_stage(self, ctx, items):
                items_list = list(items)
                items_received.extend(items_list)
                return iter(items_list)

            def _run_load_stage(self, ctx, items):
                return items

        orchestrator = TestOrchestrator()

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_150000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Create extract output with multiple data-dump files
            extract_output = phase.base_path / "extract" / "output"

            # data-dump-0001.jsonl: 2 items
            items_file1 = []
            for i in range(2):
                items_file1.append(
                    {
                        "item_id": f"file1-item-{i}",
                        "source_path": f"/test/conv{i}.json",
                        "current_step": "extract",
                        "status": "completed",
                        "metadata": {},
                        "content": f"content file1-{i}",
                        "transformed_content": None,
                        "output_path": None,
                        "error": None,
                    }
                )
            data_dump_1 = extract_output / "data-dump-0001.jsonl"
            with open(data_dump_1, "w") as f:
                for item in items_file1:
                    f.write(json.dumps(item) + "\n")

            # data-dump-0002.jsonl: 1 item
            items_file2 = [
                {
                    "item_id": "file2-item-0",
                    "source_path": "/test/conv2.json",
                    "current_step": "extract",
                    "status": "completed",
                    "metadata": {},
                    "content": "content file2-0",
                    "transformed_content": None,
                    "output_path": None,
                    "error": None,
                }
            ]
            data_dump_2 = extract_output / "data-dump-0002.jsonl"
            with open(data_dump_2, "w") as f:
                for item in items_file2:
                    f.write(json.dumps(item) + "\n")

            # Run orchestrator in Resume mode
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Assert: All 3 items from both files were restored
            self.assertEqual(len(items_received), 3)

            item_ids = {item.item_id for item in items_received}
            self.assertEqual(item_ids, {"file1-item-0", "file1-item-1", "file2-item-0"})

            # Assert: Items are in sorted file order
            item_id_order = [item.item_id for item in items_received]
            self.assertEqual(item_id_order, ["file1-item-0", "file1-item-1", "file2-item-0"])


if __name__ == "__main__":
    unittest.main()
