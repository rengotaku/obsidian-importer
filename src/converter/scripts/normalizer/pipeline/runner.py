"""
Runner - パイプライン実行

Multi-stage pipeline (A→B→C) の実行とログ記録を行う。
"""
from __future__ import annotations

import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.models import (
    NormalizationResult,
    Frontmatter,
    StageAResult,
)
from normalizer.state.manager import get_state
from normalizer.pipeline.prompts import print_stage_debug
from normalizer.pipeline.stages import (
    pre_process,
    stage3_normalize,
    stage_a,
    stage_c,
    post_process_v2,
)


# =============================================================================
# Pipeline Logging
# =============================================================================


def log_pipeline_stage(
    filename: str,
    stage: str,
    timing_ms: int = 0,
    skipped_reason: str | None = None,
    before_chars: int | None = None,
    after_chars: int | None = None,
) -> None:
    """Stage-level logging for pipeline execution"""
    state_mgr = get_state()
    session_dir = state_mgr.session_dir

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "stage": stage,
        "timing_ms": timing_ms,
        "skipped_reason": skipped_reason,
    }

    # 差分情報（指定された場合のみ）
    if before_chars is not None and after_chars is not None:
        log_entry["before_chars"] = before_chars
        log_entry["after_chars"] = after_chars
        if before_chars > 0:
            log_entry["diff_ratio"] = (after_chars - before_chars) / before_chars
        else:
            log_entry["diff_ratio"] = 0.0

    try:
        if session_dir and session_dir.exists():
            log_path = session_dir / "pipeline_stages.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# =============================================================================
# Pipeline Execution
# =============================================================================


def run_pipeline_v2(filepath: Path, content: str) -> NormalizationResult:
    """
    Multi-stage pipeline (A → B → C) を実行

    処理フロー:
    1. pre_process: ルールベース判定
    2. Stage A: LLM分類判定（dust+ジャンル統合）
       - dust → @dust へ移動、B/Cスキップ
    3. Stage B: LLM コンテンツ正規化（stage3_normalize）
    4. Stage C: LLM メタデータ生成（title/tags/summary/related）
    5. post_process_v2: 結果統合
    """
    filename = filepath.name

    # Pre-processing
    pre_start = time.time()
    pre_result = pre_process(filepath, content)
    pre_time = math.ceil((time.time() - pre_start) * 1000)
    log_pipeline_stage(filename, "pre_process", pre_time)
    print_stage_debug("pre_process", dict(pre_result), pre_time)

    # Pre-processingでdustと判定された場合は即終了
    if pre_result["skip_reason"]:
        log_pipeline_stage(filename, "stage_a", 0, "pre_process detected dust")
        log_pipeline_stage(filename, "stage_b", 0, "pre_process detected dust")
        log_pipeline_stage(filename, "stage_c", 0, "pre_process detected dust")
        return NormalizationResult(
            genre="dust",
            subfolder="",
            confidence="high",
            reason=pre_result["skip_reason"],
            frontmatter=Frontmatter(
                title=filepath.stem,
                tags=[],
                created=pre_result["extracted_date"],
                summary="",
                related=[],
                normalized=True,
            ),
            normalized_content="",
            improvements_made=[],
            is_complete_english_doc=pre_result["is_english_doc"],
        )

    # Stage A: 分類判定（Dust + ジャンル統合）
    sa_start = time.time()
    stage_a_result = stage_a(content, filename, pre_result["is_english_doc"])
    sa_time = int((time.time() - sa_start) * 1000)
    log_pipeline_stage(filename, "stage_a", sa_time)
    print_stage_debug("stage_a", stage_a_result, sa_time)
    sa_data: StageAResult = stage_a_result["data"]

    # Dust判定 → @dust へ移動、Stage B/C スキップ
    if sa_data.get("genre") == "dust":
        log_pipeline_stage(filename, "stage_b", 0, "stage_a detected dust")
        log_pipeline_stage(filename, "stage_c", 0, "stage_a detected dust")
        return NormalizationResult(
            genre="dust",
            subfolder="",
            confidence=sa_data.get("confidence", "high"),
            reason=sa_data.get("reason", "LLM判定によりdust"),
            frontmatter=Frontmatter(
                title=filepath.stem,
                tags=[],
                created=pre_result["extracted_date"],
                summary="",
                related=[],
                normalized=True,
            ),
            normalized_content="",
            improvements_made=[],
            is_complete_english_doc=pre_result["is_english_doc"],
        )

    # Stage B: コンテンツ正規化（stage3_normalizeを再利用）
    sb_start = time.time()
    stage_b_result = stage3_normalize(
        content, filename, sa_data.get("genre", "その他"), pre_result["is_english_doc"]
    )
    sb_time = int((time.time() - sb_start) * 1000)
    normalized_content = stage_b_result["data"].get("normalized_content", content)
    log_pipeline_stage(
        filename, "stage_b", sb_time,
        before_chars=len(content),
        after_chars=len(normalized_content),
    )
    print_stage_debug("stage_b", stage_b_result, sb_time)

    # Stage C: メタデータ生成（title/tags/summary/related）
    sc_start = time.time()
    stage_c_result = stage_c(normalized_content, filename, sa_data.get("genre", "その他"))
    sc_time = int((time.time() - sc_start) * 1000)
    log_pipeline_stage(filename, "stage_c", sc_time)
    print_stage_debug("stage_c", stage_c_result, sc_time)

    # Post-process: 結果統合
    return post_process_v2(
        pre_result,
        stage_a_result,
        stage_b_result,
        stage_c_result,
        filepath,
    )
