"""Organize command for ETL pipeline.

Organizes and normalizes Markdown files in the knowledge base.

Example:
    python -m src.etl organize --input ~/.staging/@index --dry-run
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.core.phase import PhaseManager
from src.etl.core.session import CompletedInformation, PhaseStats, SessionManager, SessionStatus
from src.etl.core.status import PhaseStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.phases.organize_phase import OrganizePhase


def register(subparsers) -> None:
    """Register organize command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "organize",
        help="Organize and normalize files",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory (files to organize)",
    )
    parser.add_argument(
        "--session",
        help="Reuse existing session ID",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without processing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process first N items",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute organize command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    input_path = Path(args.input)
    session_id = args.session
    debug = args.debug
    dry_run = args.dry_run
    limit = args.limit
    # Allow override for tests via _session_base_dir
    session_base_dir = getattr(args, "_session_base_dir", None) or get_session_dir()

    # Validate input directory
    if not input_path.exists():
        print(f"[Error] Input directory not found: {input_path}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND

    # Create or load session
    manager = SessionManager(session_base_dir)

    if session_id:
        if not manager.exists(session_id):
            print(f"[Error] Session not found: {session_id}", file=sys.stderr)
            return ExitCode.INPUT_NOT_FOUND
        session = manager.load(session_id)
    else:
        session = manager.create(debug_mode=debug)
        manager.save(session)

    print(f"[Session] {session.session_id} {'(reused)' if session_id else 'created'}")

    if dry_run:
        print("[Dry-run] Preview mode - no changes will be made")
        # Count input files
        md_files = list(input_path.rglob("*.md"))
        if limit:
            md_files = md_files[:limit]
        print(f"[Dry-run] Found {len(md_files)} Markdown files")
        return ExitCode.SUCCESS

    # Create phase
    phase_manager = PhaseManager(session.base_path)
    phase_data = phase_manager.create(PhaseType.ORGANIZE)

    # Copy input files to extract/input
    extract_input = phase_data.stages[StageType.EXTRACT].input_path
    count = 0
    for md_file in input_path.rglob("*.md"):
        shutil.copy(md_file, extract_input)
        count += 1
        if limit and count >= limit:
            break

    # Run organize phase
    print("[Phase] organize started")
    organize_phase = OrganizePhase()

    try:
        result = organize_phase.run(phase_data, debug_mode=debug, session_manager=manager)

        # Reload session to get the expected_total_item_count that was saved after Extract
        session = manager.load(session.session_id)
        current_phase_stats = session.phases.get("organize")
        expected_count = current_phase_stats.expected_total_item_count if current_phase_stats else 0

        # Update session with final phase stats
        completed_info = CompletedInformation(
            success_count=result.items_processed,
            error_count=result.items_failed,
            skipped_count=0,  # Organize doesn't skip items
            completed_at=datetime.now().isoformat(),
        )

        phase_stats = PhaseStats(
            status="completed"
            if result.status == PhaseStatus.COMPLETED
            else "partial"
            if result.status == PhaseStatus.PARTIAL
            else "failed",
            expected_total_item_count=expected_count,
            completed_information=completed_info,
        )
        session.phases["organize"] = phase_stats

        if result.status == PhaseStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
        elif result.status == PhaseStatus.PARTIAL:
            session.status = SessionStatus.PARTIAL
        else:
            session.status = SessionStatus.FAILED
        manager.save(session)

        # Save phase status
        phase_data.status = result.status
        phase_data.success_count = result.items_processed
        phase_data.error_count = result.items_failed
        phase_manager.save(phase_data)

        print(
            f"[Phase] organize completed ({result.items_processed} success, {result.items_failed} failed)"
        )

        # Determine exit code
        if result.status == PhaseStatus.COMPLETED:
            return ExitCode.SUCCESS
        elif result.status == PhaseStatus.PARTIAL:
            return ExitCode.PARTIAL
        else:
            return ExitCode.ALL_FAILED

    except Exception as e:
        # Record crashed phase with error details
        error_msg = f"{type(e).__name__}: {str(e)}"
        completed_info = CompletedInformation(
            success_count=0,
            error_count=0,
            skipped_count=0,
            completed_at=datetime.now().isoformat(),
        )
        phase_stats = PhaseStats(
            status="crashed",
            expected_total_item_count=0,
            completed_information=completed_info,
            error=error_msg,
        )
        session.phases["organize"] = phase_stats
        session.status = SessionStatus.FAILED
        manager.save(session)

        print(f"[Error] Phase organize crashed: {error_msg}", file=sys.stderr)
        return ExitCode.ERROR
