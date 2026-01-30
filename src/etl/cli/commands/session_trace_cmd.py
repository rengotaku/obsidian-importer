"""Session trace command for ETL pipeline.

Shows detailed session processing information including real-time statistics
from steps.jsonl for in-progress sessions.

Example:
    python -m src.etl session-trace --session 20260127_094642
    python -m src.etl session-trace --session 20260127_094642 --json
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.core.session import SessionManager


@dataclass
class StageStats:
    """Statistics for a single stage."""

    total_items: int
    """Total number of items processed."""

    success_count: int
    """Number of successfully processed items."""

    failed_count: int
    """Number of failed items."""

    pending_count: int
    """Number of pending items."""

    skipped_count: int
    """Number of skipped items."""

    total_timing_ms: int
    """Total processing time in milliseconds."""


@dataclass
class PhaseTrace:
    """Detailed trace information for a phase."""

    phase_name: str
    """Phase name (import, organize)."""

    status: str
    """Phase status."""

    stages: dict[str, StageStats]
    """Statistics per stage (extract, transform, load)."""

    total_items: int
    """Total items across all stages."""

    completed_at: str | None
    """Completion timestamp."""

    error: str | None
    """Error message if crashed."""


def _analyze_pipeline_stages_jsonl(phase_dir: Path) -> dict[str, StageStats]:
    """Analyze pipeline_stages.jsonl for stage statistics.

    Args:
        phase_dir: Path to phase directory (e.g., .staging/@session/ID/import/)

    Returns:
        Dictionary mapping stage name to StageStats.
    """
    pipeline_log = phase_dir / "pipeline_stages.jsonl"

    if not pipeline_log.exists():
        return {}

    # Track statistics per stage
    stage_data: dict[str, dict[str, dict[str, str] | int]] = defaultdict(
        lambda: {
            "item_status": {},  # item_id -> status
            "total_timing_ms": 0,
        }
    )

    try:
        with open(pipeline_log, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    stage = record.get("stage")
                    # Use item_id instead of filename for unique item tracking
                    item_id = record.get("item_id", "unknown")
                    status = record.get("status", "pending")
                    timing_ms = record.get("timing_ms", 0)

                    if not stage:
                        continue

                    data = stage_data[stage]
                    # Update latest status for this item in this stage
                    data["item_status"][item_id] = status  # type: ignore
                    data["total_timing_ms"] += timing_ms  # type: ignore

                except json.JSONDecodeError:
                    continue
    except Exception:
        return {}

    # Convert to StageStats
    stage_stats: dict[str, StageStats] = {}
    for stage, data in stage_data.items():
        item_status: dict[str, str] = data["item_status"]  # type: ignore

        # Count status
        success_count = sum(
            1 for status in item_status.values() if status == "success" or status == "completed"
        )
        failed_count = sum(1 for status in item_status.values() if status == "failed")
        skipped_count = sum(1 for status in item_status.values() if status == "skipped")
        pending_count = sum(1 for status in item_status.values() if status == "pending")

        stage_stats[stage] = StageStats(
            total_items=len(item_status),
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            skipped_count=skipped_count,
            total_timing_ms=data["total_timing_ms"],  # type: ignore
        )

    return stage_stats


def _analyze_steps_jsonl(phase_dir: Path) -> dict[str, StageStats]:
    """Analyze steps.jsonl for detailed stage statistics.

    Args:
        phase_dir: Path to phase directory (e.g., .staging/@session/ID/import/)

    Returns:
        Dictionary mapping stage name to StageStats.
    """
    # Track statistics per stage
    # Use dict to track latest status for each item
    stage_data: dict[str, dict[str, dict[str, str] | int]] = defaultdict(
        lambda: {
            "item_status": {},  # item_id -> status
            "total_timing_ms": 0,
        }
    )

    # steps.jsonl is located at {stage}/output/debug/steps.jsonl
    for stage_name in ["extract", "transform", "load"]:
        steps_log = phase_dir / stage_name / "output" / "debug" / "steps.jsonl"

        if not steps_log.exists():
            continue

        try:
            with open(steps_log, encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        item_id = record.get("item_id", "unknown")
                        status = record.get("status", "pending")
                        timing_ms = record.get("timing_ms", 0)

                        # Use stage_name directly instead of inferring from step
                        data = stage_data[stage_name]
                        # Update latest status for this item
                        data["item_status"][item_id] = status  # type: ignore
                        data["total_timing_ms"] += timing_ms  # type: ignore

                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue

    # Convert to StageStats
    stage_stats: dict[str, StageStats] = {}
    for stage, data in stage_data.items():
        item_status: dict[str, str] = data["item_status"]  # type: ignore

        # Count status
        success_count = sum(
            1 for status in item_status.values() if status == "success" or status == "completed"
        )
        failed_count = sum(1 for status in item_status.values() if status == "failed")
        skipped_count = sum(1 for status in item_status.values() if status == "skipped")
        pending_count = sum(1 for status in item_status.values() if status == "pending")

        stage_stats[stage] = StageStats(
            total_items=len(item_status),
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            skipped_count=skipped_count,
            total_timing_ms=data["total_timing_ms"],  # type: ignore
        )

    return stage_stats


def _infer_stage_from_step(step_name: str) -> str | None:
    """Infer stage name from step name.

    Args:
        step_name: Step name (e.g., "read_zip", "extract_knowledge")

    Returns:
        Stage name (extract, transform, load) or None if unknown.
    """
    extract_steps = ["read_zip", "parse_conversations", "read_json", "discover_provider"]
    transform_steps = [
        "extract_knowledge",
        "generate_metadata",
        "format_markdown",
        "translate_summary",
    ]
    load_steps = ["write_to_session", "update_index", "write_to_vault"]

    if step_name in extract_steps:
        return "extract"
    elif step_name in transform_steps:
        return "transform"
    elif step_name in load_steps:
        return "load"

    return None


def _collect_phase_trace(session_dir: Path, phase_name: str, phase_stats: dict) -> PhaseTrace:
    """Collect detailed trace information for a phase.

    Args:
        session_dir: Path to session directory
        phase_name: Phase name (import, organize)
        phase_stats: Phase statistics from session.json

    Returns:
        PhaseTrace with detailed information.
    """
    phase_dir = session_dir / phase_name

    # Prefer pipeline_stages.jsonl (available in all modes)
    # Fallback to steps.jsonl (debug mode only) if pipeline_stages.jsonl is not available
    stage_stats = _analyze_pipeline_stages_jsonl(phase_dir)
    if not stage_stats:
        stage_stats = _analyze_steps_jsonl(phase_dir)

    # Calculate total items
    total_items = 0
    if stage_stats:
        # Use load stage count if available (final stage)
        if "load" in stage_stats:
            total_items = stage_stats["load"].total_items
        elif "transform" in stage_stats:
            total_items = stage_stats["transform"].total_items
        elif "extract" in stage_stats:
            total_items = stage_stats["extract"].total_items

    # Fallback to phase_stats if no logs available
    if not stage_stats:
        total_items = (
            phase_stats.get("success_count", 0)
            + phase_stats.get("error_count", 0)
            + phase_stats.get("skipped_count", 0)
        )

    return PhaseTrace(
        phase_name=phase_name,
        status=phase_stats.get("status", "unknown"),
        stages=stage_stats,
        total_items=total_items,
        completed_at=phase_stats.get("completed_at"),
        error=phase_stats.get("error"),
    )


def register(subparsers) -> None:
    """Register session-trace command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "session-trace",
        help="Show detailed session trace",
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session ID to trace",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute session-trace command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    session_id = args.session
    as_json = args.json
    # Allow override for tests via _session_base_dir
    session_base_dir = getattr(args, "_session_base_dir", None) or get_session_dir()

    manager = SessionManager(session_base_dir)

    if not manager.exists(session_id):
        print(f"[Error] Session not found: {session_id}", file=sys.stderr)
        return ExitCode.ERROR

    session = manager.load(session_id)

    # Collect detailed trace for each phase
    phase_traces: dict[str, PhaseTrace] = {}
    for phase_name, phase_stats_obj in session.phases.items():
        # Convert PhaseStats to dict for compatibility
        # success_count, error_count, skipped_count are in completed_information
        completed_info = phase_stats_obj.completed_information
        phase_stats_dict = {
            "status": phase_stats_obj.status,
            "success_count": completed_info.success_count if completed_info else 0,
            "error_count": completed_info.error_count if completed_info else 0,
            "skipped_count": completed_info.skipped_count if completed_info else 0,
            "completed_at": completed_info.completed_at if completed_info else None,
            "error": phase_stats_obj.error,
        }
        phase_trace = _collect_phase_trace(session.base_path, phase_name, phase_stats_dict)
        phase_traces[phase_name] = phase_trace

    if as_json:
        # JSON output
        output = {
            "session_id": session.session_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "debug_mode": session.debug_mode,
            "phases": {},
        }
        if session.provider:
            output["provider"] = session.provider

        for phase_name, trace in phase_traces.items():
            # Calculate summary across all stages
            # Success: Only count items that reached the final stage (load)
            total_success = trace.stages.get("load", StageStats(0, 0, 0, 0, 0, 0)).success_count
            # Failed/Skipped: Sum across all stages (each item only fails/skips once per stage)
            total_failed = sum(stats.failed_count for stats in trace.stages.values())
            total_pending = sum(stats.pending_count for stats in trace.stages.values())
            total_skipped = sum(stats.skipped_count for stats in trace.stages.values())
            total_time_ms = sum(stats.total_timing_ms for stats in trace.stages.values())

            output["phases"][phase_name] = {
                "status": trace.status,
                "total_items": trace.total_items,
                "completed_at": trace.completed_at,
                "error": trace.error,
                "summary": {
                    "total_success": total_success,
                    "total_failed": total_failed,
                    "total_pending": total_pending,
                    "total_skipped": total_skipped,
                    "total_time_ms": total_time_ms,
                },
                "stages": {
                    stage: {
                        "total_items": stats.total_items,
                        "success": stats.success_count,
                        "failed": stats.failed_count,
                        "pending": stats.pending_count,
                        "skipped": stats.skipped_count,
                        "timing_ms": stats.total_timing_ms,
                    }
                    for stage, stats in trace.stages.items()
                },
            }

        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print("=" * 80)
        print(f"Session Trace: {session.session_id}")
        print("=" * 80)
        print(f"Status: {session.status.value}")
        print(f"Created: {session.created_at.isoformat()}")
        print(f"Debug Mode: {session.debug_mode}")
        if session.provider:
            print(f"Provider: {session.provider}")
        print()

        for phase_name, trace in phase_traces.items():
            print(f"Phase: {phase_name}")
            print(f"  Status: {trace.status}")
            print(f"  Total Items: {trace.total_items}")

            if trace.completed_at:
                print(f"  Completed: {trace.completed_at}")
            if trace.error:
                print(f"  Error: {trace.error}")

            if trace.stages:
                print("  Stages:")
                for stage, stats in trace.stages.items():
                    print(f"    {stage}:")
                    print(f"      Total: {stats.total_items}")
                    print(f"      Success: {stats.success_count}")
                    print(f"      Failed: {stats.failed_count}")
                    print(f"      Skipped: {stats.skipped_count}")
                    if stats.pending_count > 0:
                        print(f"      Pending: {stats.pending_count}")
                    print(f"      Time: {stats.total_timing_ms}ms")

                # Calculate summary totals
                # Success: Only count items that reached the final stage (load)
                total_success = trace.stages.get("load", StageStats(0, 0, 0, 0, 0, 0)).success_count
                # Failed/Skipped: Sum across all stages
                total_failed = sum(stats.failed_count for stats in trace.stages.values())
                total_pending = sum(stats.pending_count for stats in trace.stages.values())
                total_skipped = sum(stats.skipped_count for stats in trace.stages.values())
                total_time_ms = sum(stats.total_timing_ms for stats in trace.stages.values())

                # Print summary
                print()
                print("  Summary:")
                print(f"    Total Success: {total_success}")
                print(f"    Total Failed: {total_failed}")
                print(f"    Total Skipped: {total_skipped}")
                if total_pending > 0:
                    print(f"    Total Pending: {total_pending}")
                print(f"    Total Time: {total_time_ms}ms ({total_time_ms / 1000:.2f}s)")
            else:
                print("  (No detailed stage information available)")

            print()

        print("=" * 80)

    return ExitCode.SUCCESS
