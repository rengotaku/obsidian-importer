"""
Tests for SessionLogger class

TDD: テストを先に書き、実装で PASS させる
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# =============================================================================
# US1: 処理進捗の可視化
# =============================================================================


class TestSessionLoggerConstructor:
    """T008: SessionLogger コンストラクタのテスト"""

    def test_constructor_stores_provider(self):
        """provider が正しく保存される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                assert logger.provider == "claude"

    def test_constructor_stores_total_files(self):
        """total_files が正しく保存される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                assert logger.total_files == 100

    def test_constructor_default_prefix(self):
        """デフォルトプレフィックスは "import" """
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                assert logger.prefix == "import"

    def test_constructor_custom_prefix(self):
        """カスタムプレフィックスを指定可能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(
                    provider="claude", total_files=100, prefix="custom"
                )
                assert logger.prefix == "custom"


class TestSessionLoggerStartSession:
    """T009: start_session() のテスト"""

    def test_start_session_creates_directory(self):
        """start_session() でセッションディレクトリが作成される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                session_dir = logger.start_session()

                assert session_dir.exists()
                assert session_dir.is_dir()
                assert session_dir.name.startswith("import_")

    def test_start_session_creates_session_json(self):
        """start_session() で session.json が作成される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                session_dir = logger.start_session()

                session_file = session_dir / "session.json"
                assert session_file.exists()

                data = json.loads(session_file.read_text())
                assert data["provider"] == "claude"
                assert data["total_files"] == 100
                assert "session_id" in data
                assert "started_at" in data

    def test_start_session_creates_execution_log(self):
        """start_session() で execution.log が作成される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                session_dir = logger.start_session()

                log_file = session_dir / "execution.log"
                assert log_file.exists()

    def test_start_session_returns_path(self):
        """start_session() はセッションディレクトリのパスを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                session_dir = logger.start_session()

                assert isinstance(session_dir, Path)
                assert logger.session_dir == session_dir


class TestSessionLoggerLog:
    """T010: log() メソッドのテスト"""

    def test_log_writes_to_execution_log(self):
        """log() が execution.log に書き込む"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()
                logger.log("Test message", also_print=False)

                log_file = logger.session_dir / "execution.log"
                content = log_file.read_text()
                assert "Test message" in content

    def test_log_includes_timestamp(self):
        """log() のメッセージにタイムスタンプが含まれる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()
                logger.log("Test message", also_print=False)

                log_file = logger.session_dir / "execution.log"
                content = log_file.read_text()
                # タイムスタンプ形式 [YYYY-MM-DDTHH:MM:SS] を確認
                assert "[202" in content  # 年の始まり


class TestSessionLoggerLogProgress:
    """T011: log_progress() メソッドのテスト"""

    def test_log_progress_format(self):
        """log_progress() がプログレスバー形式で出力する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                # also_print=False でファイルのみ出力
                logger.log_progress(
                    current=25,
                    title="テスト会話",
                    phase1_ok=True,
                    phase2_ok=True,
                    elapsed_sec=12.5,
                    also_print=False,
                )

                log_file = logger.session_dir / "execution.log"
                content = log_file.read_text()

                # プログレス情報が含まれることを確認
                assert "25" in content  # current
                assert "100" in content  # total
                assert "テスト会話" in content

    def test_log_progress_shows_phase_status(self):
        """log_progress() が Phase ステータスを表示する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_progress(
                    current=1,
                    title="会話タイトル",
                    phase1_ok=True,
                    phase2_ok=False,
                    elapsed_sec=5.0,
                    also_print=False,
                )

                log_file = logger.session_dir / "execution.log"
                content = log_file.read_text()

                # Phase ステータスマーカーが含まれる
                assert "Phase1" in content or "phase1" in content.lower()


# =============================================================================
# US2: ステージ別処理詳細の記録
# =============================================================================


class TestSessionLoggerLogStage:
    """T021-T022: log_stage() メソッドのテスト"""

    def test_log_stage_writes_jsonl(self):
        """log_stage() が JSONL 形式で書き込む"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase1",
                    timing_ms=1234,
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                assert jsonl_file.exists()

                line = jsonl_file.read_text().strip()
                record = json.loads(line)
                assert record["filename"] == "test.md"
                assert record["stage"] == "phase1"
                assert record["timing_ms"] == 1234

    def test_log_stage_contains_required_fields(self):
        """StageRecord に必須フィールドが含まれる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase2",
                    timing_ms=5000,
                    skipped_reason=None,
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                # 必須フィールドの確認
                assert "timestamp" in record
                assert "filename" in record
                assert "stage" in record
                assert "timing_ms" in record
                assert "skipped_reason" in record

    def test_log_stage_with_skipped_reason(self):
        """スキップ理由を記録できる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase2",
                    timing_ms=0,
                    skipped_reason="phase2_limit",
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                assert record["skipped_reason"] == "phase2_limit"

    def test_log_stage_with_diff_stats(self):
        """差分情報を記録できる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase2",
                    timing_ms=5000,
                    before_chars=10000,
                    after_chars=3000,
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                assert record["before_chars"] == 10000
                assert record["after_chars"] == 3000
                assert record["diff_ratio"] == -0.7

    def test_log_stage_without_diff_stats(self):
        """差分情報なしでも動作する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase1",
                    timing_ms=100,
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                assert "before_chars" not in record
                assert "after_chars" not in record
                assert "diff_ratio" not in record

    def test_log_stage_with_file_id(self):
        """file_id を記録できる (US2 T014)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase1",
                    timing_ms=1234,
                    file_id="a1b2c3d4e5f6",
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                assert record["file_id"] == "a1b2c3d4e5f6"

    def test_log_stage_without_file_id(self):
        """file_id なしでも動作する（後方互換性）(US2 T014)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.log_stage(
                    filename="test.md",
                    stage="phase1",
                    timing_ms=100,
                    # file_id は指定しない
                )

                jsonl_file = logger.session_dir / "pipeline_stages.jsonl"
                record = json.loads(jsonl_file.read_text().strip())

                # file_id が含まれない
                assert "file_id" not in record


# =============================================================================
# US3: 状態ファイルの分離管理
# =============================================================================


class TestSessionLoggerAddProcessed:
    """T027: add_processed() メソッドのテスト"""

    def test_add_processed_updates_internal_list(self):
        """add_processed() が内部リストを更新する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.add_processed(file="conv1.md", output="/output/conv1.md")
                logger.add_processed(file="conv2.md", output="/output/conv2.md")

                assert logger.stats["success"] == 2


class TestSessionLoggerAddError:
    """T028: add_error() メソッドのテスト"""

    def test_add_error_updates_internal_list(self):
        """add_error() が内部リストを更新する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.add_error(
                    file="conv1.md", error="Parse error", stage="phase1"
                )

                assert logger.stats["error"] == 1


class TestSessionLoggerAddPending:
    """T029: add_pending() メソッドのテスト"""

    def test_add_pending_updates_internal_list(self):
        """add_pending() が内部リストを更新する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                logger.add_pending(file="conv1.md", reason="phase2_limit")

                assert logger.stats["pending"] == 1


class TestSessionLoggerFinalize:
    """T030-T031: finalize() メソッドのテスト"""

    def test_finalize_writes_state_files(self):
        """finalize() が状態ファイルを書き込む"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=3)
                logger.start_session()

                logger.add_processed(file="conv1.md", output="/out/conv1.md")
                logger.add_error(file="conv2.md", error="Error", stage="phase1")
                logger.add_pending(file="conv3.md", reason="limit")

                logger.finalize(elapsed_seconds=60.0, also_print=False)

                # 状態ファイルの存在確認
                assert (logger.session_dir / "processed.json").exists()
                assert (logger.session_dir / "errors.json").exists()
                assert (logger.session_dir / "pending.json").exists()
                assert (logger.session_dir / "results.json").exists()

    def test_finalize_writes_results_json_with_correct_counts(self):
        """finalize() の results.json に正しいカウントが含まれる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=5)
                logger.start_session()

                logger.add_processed(file="c1.md", output="/o/c1.md")
                logger.add_processed(file="c2.md", output="/o/c2.md")
                logger.add_error(file="c3.md", error="Err", stage="phase1")
                logger.add_pending(file="c4.md", reason="limit")
                logger.add_pending(file="c5.md", reason="limit")

                logger.finalize(elapsed_seconds=120.0, also_print=False)

                results_file = logger.session_dir / "results.json"
                results = json.loads(results_file.read_text())

                assert results["total"] == 5
                assert results["success"] == 2
                assert results["error"] == 1
                assert results["pending"] == 2
                assert results["elapsed_seconds"] == 120.0


# =============================================================================
# Edge Cases & Integration
# =============================================================================


class TestSessionLoggerGracefulDegradation:
    """T041: graceful degradation のテスト"""

    def test_log_continues_on_io_error(self):
        """I/O エラー時も処理が継続する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.llm_import.common.session_logger import SessionLogger

                logger = SessionLogger(provider="claude", total_files=100)
                logger.start_session()

                # セッションディレクトリを削除して I/O エラーを発生させる
                import shutil

                shutil.rmtree(logger.session_dir)

                # エラーが発生しても例外が上がらないことを確認
                # (graceful degradation)
                try:
                    logger.log("Test after dir removed", also_print=False)
                except Exception:
                    pytest.fail("log() should not raise exception on I/O error")
