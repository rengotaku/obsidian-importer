"""CLI entry point for ETL pipeline.

Provides commands:
- import: Import Claude export data
- organize: Organize and normalize files
- status: Show session status
- retry: Retry failed items
- clean: Clean old sessions
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from enum import IntEnum
from pathlib import Path

from src.etl.core.phase import PhaseManager
from src.etl.core.session import SessionManager
from src.etl.core.status import PhaseStatus, SessionStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.phases.import_phase import ImportPhase
from src.etl.phases.organize_phase import OrganizePhase


class ExitCode(IntEnum):
    """CLI exit codes."""

    SUCCESS = 0
    ERROR = 1
    INPUT_NOT_FOUND = 2
    OLLAMA_ERROR = 3
    PARTIAL = 4
    ALL_FAILED = 5


# Default session directory
DEFAULT_SESSION_DIR = Path(".staging/@session")


def get_session_dir() -> Path:
    """Get session directory from environment or default."""
    env_dir = os.environ.get("ETL_SESSION_DIR")
    if env_dir:
        return Path(env_dir)
    return DEFAULT_SESSION_DIR


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="etl",
        description="ETL Pipeline for Obsidian Knowledge Base",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # import command
    import_parser = subparsers.add_parser(
        "import",
        help="Import Claude/ChatGPT export data",
    )
    import_parser.add_argument(
        "--input",
        required=True,
        help="Input directory or ZIP file (Claude export or ChatGPT export)",
    )
    import_parser.add_argument(
        "--provider",
        choices=["claude", "openai", "github"],
        default="claude",
        help="Source provider (default: claude)",
    )
    import_parser.add_argument(
        "--session",
        help="Reuse existing session ID",
    )
    import_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without processing",
    )
    import_parser.add_argument(
        "--limit",
        type=int,
        help="Process first N items",
    )
    import_parser.add_argument(
        "--no-fetch-titles",
        action="store_true",
        help="Disable URL title fetching (default: enabled)",
    )
    import_parser.add_argument(
        "--chunk",
        action="store_true",
        help="Enable chunking for large files (>25000 chars). Default: skip with too_large frontmatter",
    )

    # organize command
    organize_parser = subparsers.add_parser(
        "organize",
        help="Organize and normalize files",
    )
    organize_parser.add_argument(
        "--input",
        required=True,
        help="Input directory (files to organize)",
    )
    organize_parser.add_argument(
        "--session",
        help="Reuse existing session ID",
    )
    organize_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without processing",
    )
    organize_parser.add_argument(
        "--limit",
        type=int,
        help="Process first N items",
    )

    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show session status",
    )
    status_parser.add_argument(
        "--session",
        help="Show specific session",
    )
    status_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all sessions",
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # retry command
    retry_parser = subparsers.add_parser(
        "retry",
        help="Retry failed items",
    )
    retry_parser.add_argument(
        "--session",
        required=True,
        help="Session to retry",
    )
    retry_parser.add_argument(
        "--phase",
        choices=["import", "organize"],
        help="Retry specific phase",
    )
    retry_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    # clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean old sessions",
    )
    clean_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Clean sessions older than N days (default: 7)",
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without deleting",
    )
    clean_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation",
    )

    # trace command
    trace_parser = subparsers.add_parser(
        "trace",
        help="Trace item processing through pipeline steps",
    )
    trace_parser.add_argument(
        "--session",
        required=True,
        help="Session ID to trace",
    )
    trace_parser.add_argument(
        "--target",
        choices=["ALL", "ERROR"],
        default="ALL",
        help="Target items to trace (default: ALL)",
    )
    trace_parser.add_argument(
        "--item",
        help="Item ID to trace (required when target=ALL)",
    )
    trace_parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show content diffs between steps",
    )

    return parser


def run_import(
    input_path: str | Path,
    provider: str,
    session_id: str | None,
    debug: bool,
    dry_run: bool,
    limit: int | None,
    fetch_titles: bool,
    chunk: bool,
    session_base_dir: Path,
) -> int:
    """Run import command.

    Args:
        input_path: Path to input directory/ZIP file, or GitHub URL for github provider.
        provider: Source provider ("claude", "openai", or "github").
        session_id: Optional existing session ID.
        debug: Enable debug mode.
        dry_run: Preview without processing.
        limit: Limit number of items to process.
        fetch_titles: Enable URL title fetching.
        chunk: Enable chunking for large files (>25000 chars).
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
    # Validate input path (skip for GitHub URLs)
    if provider == "github":
        # GitHub: input_path is URL string
        if not isinstance(input_path, str):
            print("[Error] GitHub provider requires URL string", file=sys.stderr)
            return ExitCode.ERROR
        source_path = input_path
    else:
        # Claude/OpenAI: input_path is Path object
        if not isinstance(input_path, Path):
            input_path = Path(input_path)
        if not input_path.exists():
            print(f"[Error] Input path not found: {input_path}", file=sys.stderr)
            return ExitCode.INPUT_NOT_FOUND
        source_path = input_path

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
        if provider == "github":
            print(f"[Dry-run] GitHub URL: {source_path}")
        elif source_path.is_file() and source_path.suffix.lower() == ".zip":
            print(f"[Dry-run] ChatGPT ZIP file: {source_path.name}")
        else:
            json_files = list(source_path.glob("*.json"))
            if limit:
                json_files = json_files[:limit]
            print(f"[Dry-run] Found {len(json_files)} JSON files")
        return ExitCode.SUCCESS

    # Create phase
    phase_manager = PhaseManager(session.base_path)
    phase_data = phase_manager.create(PhaseType.IMPORT)

    # Copy input files to extract/input (skip on Resume mode and GitHub)
    extract_input = phase_data.stages[StageType.EXTRACT].input_path

    if provider == "github":
        # GitHub: Save URL to file for extractor to read
        url_file = extract_input / "github_url.txt"
        url_file.write_text(source_path, encoding="utf-8")
    elif not session_id:
        # New session: copy input files
        if source_path.is_file() and source_path.suffix.lower() == ".zip":
            # ChatGPT ZIP: copy ZIP file directly
            shutil.copy(source_path, extract_input)
        else:
            # Claude directory: copy JSON files (conversations.json priority)
            file_count = 0
            conversations_file = source_path / "conversations.json"
            if conversations_file.exists():
                shutil.copy(conversations_file, extract_input)
                file_count += 1

            # Copy other JSON files if limit allows
            for json_file in source_path.glob("*.json"):
                if json_file.name == "conversations.json":
                    continue  # Already copied
                shutil.copy(json_file, extract_input)
                file_count += 1
                if limit and file_count >= limit:
                    break
    else:
        # Resume mode: validate existing input files
        if not extract_input.exists() or not any(extract_input.iterdir()):
            print(
                f"[Error] No input files found in session: {session_id}",
                file=sys.stderr,
            )
            return ExitCode.INPUT_NOT_FOUND

    # Run import phase
    print(f"[Phase] import started (provider: {provider})")
    import_phase = ImportPhase(provider=provider, fetch_titles=fetch_titles, chunk=chunk)

    try:
        result = import_phase.run(phase_data, debug_mode=debug, limit=limit)

        # Update session with phase stats
        from src.etl.core.session import PhaseStats

        phase_stats = PhaseStats(
            status="completed"
            if result.status == PhaseStatus.COMPLETED
            else "partial"
            if result.status == PhaseStatus.PARTIAL
            else "failed",
            success_count=result.items_processed,
            error_count=result.items_failed,
            skipped_count=result.items_skipped,
            completed_at=datetime.now().isoformat(),
        )
        session.phases["import"] = phase_stats

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

        # Format console output with skipped count if > 0
        if result.items_skipped > 0:
            print(
                f"[Phase] import completed ({result.items_processed} success, {result.items_failed} failed, {result.items_skipped} skipped)"
            )
        else:
            print(
                f"[Phase] import completed ({result.items_processed} success, {result.items_failed} failed)"
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
        from src.etl.core.session import PhaseStats

        error_msg = f"{type(e).__name__}: {str(e)}"
        phase_stats = PhaseStats(
            status="crashed",
            success_count=0,
            error_count=0,
            completed_at=datetime.now().isoformat(),
            error=error_msg,
        )
        session.phases["import"] = phase_stats
        session.status = SessionStatus.FAILED
        manager.save(session)

        print(f"[Error] Phase import crashed: {error_msg}", file=sys.stderr)
        return ExitCode.ERROR


def run_organize(
    input_path: Path,
    session_id: str | None,
    debug: bool,
    dry_run: bool,
    limit: int | None,
    session_base_dir: Path,
) -> int:
    """Run organize command.

    Args:
        input_path: Path to input directory.
        session_id: Optional existing session ID.
        debug: Enable debug mode.
        dry_run: Preview without processing.
        limit: Limit number of items to process.
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
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
        result = organize_phase.run(phase_data, debug_mode=debug)

        # Update session with phase stats
        from src.etl.core.session import PhaseStats

        phase_stats = PhaseStats(
            status="completed"
            if result.status == PhaseStatus.COMPLETED
            else "partial"
            if result.status == PhaseStatus.PARTIAL
            else "failed",
            success_count=result.items_processed,
            error_count=result.items_failed,
            completed_at=datetime.now().isoformat(),
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
        from src.etl.core.session import PhaseStats

        error_msg = f"{type(e).__name__}: {str(e)}"
        phase_stats = PhaseStats(
            status="crashed",
            success_count=0,
            error_count=0,
            completed_at=datetime.now().isoformat(),
            error=error_msg,
        )
        session.phases["organize"] = phase_stats
        session.status = SessionStatus.FAILED
        manager.save(session)

        print(f"[Error] Phase organize crashed: {error_msg}", file=sys.stderr)
        return ExitCode.ERROR


def run_status(
    session_id: str | None,
    show_all: bool,
    as_json: bool,
    session_base_dir: Path,
) -> int:
    """Run status command.

    Args:
        session_id: Optional specific session ID.
        show_all: Show all sessions.
        as_json: Output as JSON.
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
    manager = SessionManager(session_base_dir)

    if session_id:
        # Show specific session
        if not manager.exists(session_id):
            print(f"[Error] Session not found: {session_id}", file=sys.stderr)
            return ExitCode.ERROR

        session = manager.load(session_id)

        if as_json:
            print(json.dumps(session.to_dict(), indent=2))
        else:
            print(f"Session: {session.session_id}")
            print(f"Status: {session.status.value}")
            print(f"Debug: {session.debug_mode}")
            print(f"Created: {session.created_at.isoformat()}")

            # Show phase details
            if session.phases:
                print("\nPhases:")
                for phase_name, phase_stats in session.phases.items():
                    print(f"  {phase_name}:")
                    print(f"    Status: {phase_stats.status}")
                    print(f"    Success: {phase_stats.success_count}")
                    print(f"    Failed: {phase_stats.error_count}")
                    if phase_stats.skipped_count > 0:
                        print(f"    Skipped: {phase_stats.skipped_count}")
                    print(f"    Completed: {phase_stats.completed_at}")
                    if phase_stats.error:
                        print(f"    Error: {phase_stats.error}")
            else:
                print("Phases: none")

        return ExitCode.SUCCESS

    elif show_all:
        # Show all sessions
        sessions = manager.list_sessions()

        if not sessions:
            print("[Info] No sessions found")
            return ExitCode.ERROR

        if as_json:
            result = []
            for sid in sessions:
                try:
                    s = manager.load(sid)
                    result.append(s.to_dict())
                except Exception:
                    result.append({"session_id": sid, "status": "unknown"})
            print(json.dumps(result, indent=2))
        else:
            print("Sessions:")
            for sid in sessions:
                try:
                    s = manager.load(sid)
                    print(f"  {sid}: {s.status.value}")
                except Exception:
                    print(f"  {sid}: (error loading)")

        return ExitCode.SUCCESS

    else:
        # Show latest session
        sessions = manager.list_sessions()

        if not sessions:
            print("[Info] No sessions found")
            return ExitCode.ERROR

        latest_id = sessions[-1]  # Sorted, so last is latest
        session = manager.load(latest_id)

        if as_json:
            print(json.dumps(session.to_dict(), indent=2))
        else:
            print(f"Latest Session: {session.session_id}")
            print(f"Status: {session.status.value}")
            print(f"Debug: {session.debug_mode}")

            # Show phase details
            if session.phases:
                print("\nPhases:")
                for phase_name, phase_stats in session.phases.items():
                    print(f"  {phase_name}:")
                    print(f"    Status: {phase_stats.status}")
                    print(f"    Success: {phase_stats.success_count}")
                    print(f"    Failed: {phase_stats.error_count}")
                    if phase_stats.skipped_count > 0:
                        print(f"    Skipped: {phase_stats.skipped_count}")
                    print(f"    Completed: {phase_stats.completed_at}")
                    if phase_stats.error:
                        print(f"    Error: {phase_stats.error}")
            else:
                print("Phases: none")

        return ExitCode.SUCCESS


def run_retry(
    session_id: str,
    phase: str | None,
    debug: bool,
    session_base_dir: Path,
) -> int:
    """Run retry command.

    Args:
        session_id: Session to retry.
        phase: Optional specific phase to retry.
        debug: Enable debug mode.
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
    manager = SessionManager(session_base_dir)

    if not manager.exists(session_id):
        print(f"[Error] Session not found: {session_id}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND

    session = manager.load(session_id)
    phase_manager = PhaseManager(session.base_path)

    # Find phases with errors
    phases_to_retry = []

    if phase:
        phase_type = PhaseType(phase)
        if phase_manager.exists(phase_type):
            phase_data = phase_manager.load(phase_type)
            if phase_data.error_count > 0:
                phases_to_retry.append(phase_type)
    else:
        # Check all phases
        for phase_type in PhaseType:
            if phase_manager.exists(phase_type):
                phase_data = phase_manager.load(phase_type)
                if phase_data.error_count > 0:
                    phases_to_retry.append(phase_type)

    if not phases_to_retry:
        print("[Info] No failed items to retry")
        return ExitCode.ERROR

    print(f"[Retry] Session {session_id}")
    print(f"[Retry] Phases to retry: {', '.join(p.value for p in phases_to_retry)}")

    total_retried = 0
    total_failed = 0

    for phase_type in phases_to_retry:
        phase_data = phase_manager.load(phase_type)

        if phase_type == PhaseType.IMPORT:
            phase_runner = ImportPhase()
        else:
            phase_runner = OrganizePhase()

        result = phase_runner.run(phase_data, debug_mode=debug)

        print(
            f"[Phase] {phase_type.value}: {result.items_processed} success, {result.items_failed} failed"
        )

        total_retried += result.items_processed
        total_failed += result.items_failed

        # Update phase status
        phase_data.status = result.status
        phase_data.success_count += result.items_processed
        phase_data.error_count = result.items_failed
        phase_manager.save(phase_data)

    # Update session
    if total_failed == 0:
        session.status = SessionStatus.COMPLETED
    elif total_retried > 0:
        session.status = SessionStatus.PARTIAL
    else:
        session.status = SessionStatus.FAILED
    manager.save(session)

    if total_failed == 0:
        return ExitCode.SUCCESS
    elif total_retried > 0:
        return ExitCode.PARTIAL
    else:
        return ExitCode.ALL_FAILED


def run_trace(
    session_id: str,
    target: str,
    item_id: str | None,
    show_content: bool,
    session_base_dir: Path,
) -> int:
    """Run trace command.

    Args:
        session_id: Session to trace.
        target: Target items to trace ("ALL" or "ERROR").
        item_id: Item ID to trace (required when target=ALL).
        show_content: Show content diffs between steps.
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
    manager = SessionManager(session_base_dir)

    if not manager.exists(session_id):
        print(f"[Error] Session not found: {session_id}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND

    session_path = session_base_dir / session_id

    # Collect error items if target=ERROR
    if target == "ERROR":
        error_items = []

        # Search pipeline_stages.jsonl in all phases
        for phase_dir in session_path.iterdir():
            if not phase_dir.is_dir():
                continue

            pipeline_jsonl = phase_dir / "pipeline_stages.jsonl"
            if not pipeline_jsonl.exists():
                continue

            # Read JSONL and collect failed items
            try:
                with open(pipeline_jsonl, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        if record.get("status") == "failed":
                            # Extract item_id from filename or parent_item_id
                            item_id = record.get("parent_item_id")
                            if not item_id:
                                # Fallback: use filename without extension
                                filename = record.get("filename", "")
                                item_id = Path(filename).stem

                            if item_id and item_id not in error_items:
                                error_items.append(item_id)
            except Exception as e:
                print(
                    f"[Warning] Failed to read {pipeline_jsonl}: {e}",
                    file=sys.stderr,
                )

        if not error_items:
            print(f"[Info] No error items found in session: {session_id}")
            return ExitCode.SUCCESS

        print(f"[Trace] Session: {session_id}")
        print(f"[Trace] Target: ERROR ({len(error_items)} items)")
        print()

        # Trace each error item
        for idx, error_item_id in enumerate(error_items, 1):
            print(f"{'=' * 80}")
            print(f"Error Item {idx}/{len(error_items)}: {error_item_id}")
            print(f"{'=' * 80}")
            _trace_single_item(session_path, error_item_id, show_content)
            print()

        return ExitCode.SUCCESS

    else:  # target == "ALL"
        if not item_id:
            print(
                "[Error] --item is required when target=ALL",
                file=sys.stderr,
            )
            return ExitCode.ERROR

        print(f"[Trace] Session: {session_id}")
        print(f"[Trace] Item: {item_id}")
        print()

        _trace_single_item(session_path, item_id, show_content)
        return ExitCode.SUCCESS


def _trace_single_item(
    session_path: Path,
    item_id: str,
    show_content: bool,
) -> None:
    """Trace a single item through pipeline steps.

    Args:
        session_path: Path to session directory.
        item_id: Item ID to trace.
        show_content: Show content diffs between steps.
    """

    # Collect all step records from all phases
    all_records = []

    for phase_dir in session_path.iterdir():
        if not phase_dir.is_dir():
            continue

        # Look for debug/steps.jsonl in each stage
        for stage_dir in phase_dir.iterdir():
            if not stage_dir.is_dir():
                continue

            steps_jsonl = stage_dir / "output" / "debug" / "steps.jsonl"
            if not steps_jsonl.exists():
                continue

            # Read JSONL file
            try:
                with open(steps_jsonl, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        if record.get("item_id") == item_id:
                            # Add phase and stage context
                            record["phase"] = phase_dir.name
                            record["stage_folder"] = stage_dir.name
                            all_records.append(record)
            except Exception as e:
                print(f"[Warning] Failed to read {steps_jsonl}: {e}", file=sys.stderr)

    if not all_records:
        print(f"[Error] No trace records found for item: {item_id}", file=sys.stderr)
        print("[Hint] Make sure the session was run with --debug flag", file=sys.stderr)
        return

    # Sort by timestamp to preserve actual execution order
    all_records.sort(key=lambda r: r["timestamp"])

    # Print table header
    print("Step Progress:")
    print()
    header = f"{'Step':<6} {'Phase':<10} {'Stage':<10} {'Current Step':<25} {'Before':<10} {'After':<10} {'Ratio':<8} {'Time(ms)':<10}"
    print(header)
    print("=" * len(header))

    total_time_ms = 0
    prev_content = None

    for record in all_records:
        step_index = record["step_index"]
        phase = record["phase"]
        stage = record["stage_folder"]
        current_step = record["current_step"]
        before_chars = record.get("before_chars")
        after_chars = record.get("after_chars")
        diff_ratio = record.get("diff_ratio")
        timing_ms = record.get("timing_ms", 0)

        total_time_ms += timing_ms

        # Format values
        before_str = str(before_chars) if before_chars is not None else "-"
        after_str = str(after_chars) if after_chars is not None else "-"
        ratio_str = f"{diff_ratio:.3f}" if diff_ratio is not None else "-"
        timing_str = str(timing_ms)

        print(
            f"{step_index:<6} {phase:<10} {stage:<10} {current_step:<25} {before_str:<10} {after_str:<10} {ratio_str:<8} {timing_str:<10}"
        )

        # Store content for diff display
        if show_content:
            current_content = record.get("content")
            if prev_content is not None and current_content is not None:
                print(f"  Content diff (step {step_index - 1} → {step_index}):")
                print(f"    Previous: {prev_content[:100]}...")
                print(f"    Current:  {current_content[:100]}...")
                print()
            prev_content = current_content

    print("=" * len(header))
    print(f"Total Processing Time: {total_time_ms}ms")
    print()

    # Summary statistics
    first_chars = next(
        (r.get("before_chars") for r in all_records if r.get("before_chars") is not None),
        None,
    )
    last_chars = next(
        (r.get("after_chars") for r in reversed(all_records) if r.get("after_chars") is not None),
        None,
    )

    if first_chars and last_chars:
        overall_ratio = last_chars / first_chars
        print(f"Overall Change: {first_chars} → {last_chars} chars (ratio: {overall_ratio:.3f})")
        print()


def run_clean(
    days: int,
    dry_run: bool,
    force: bool,
    session_base_dir: Path,
) -> int:
    """Run clean command.

    Args:
        days: Clean sessions older than N days.
        dry_run: Preview without deleting.
        force: Skip confirmation.
        session_base_dir: Base directory for sessions.

    Returns:
        Exit code.
    """
    manager = SessionManager(session_base_dir)
    sessions = manager.list_sessions()

    if not sessions:
        print("[Info] No sessions to clean")
        return ExitCode.SUCCESS

    # Find old sessions
    cutoff = datetime.now() - timedelta(days=days)
    old_sessions = []

    for session_id in sessions:
        try:
            session = manager.load(session_id)
            if session.created_at < cutoff:
                old_sessions.append(session_id)
        except Exception:
            # Include sessions that can't be loaded
            old_sessions.append(session_id)

    if not old_sessions:
        print(f"[Info] No sessions older than {days} days")
        return ExitCode.SUCCESS

    print(f"[Clean] Found {len(old_sessions)} session(s) older than {days} days")

    if dry_run:
        print("[Dry-run] Would delete:")
        for sid in old_sessions:
            print(f"  - {sid}")
        return ExitCode.SUCCESS

    if not force:
        print("Sessions to delete:")
        for sid in old_sessions:
            print(f"  - {sid}")
        response = input("Delete these sessions? [y/N] ")
        if response.lower() != "y":
            print("[Clean] Cancelled")
            return ExitCode.SUCCESS

    # Delete sessions
    for session_id in old_sessions:
        session_path = session_base_dir / session_id
        try:
            shutil.rmtree(session_path)
            print(f"[Clean] Deleted: {session_id}")
        except Exception as e:
            print(f"[Error] Failed to delete {session_id}: {e}", file=sys.stderr)

    print(f"[Clean] Deleted {len(old_sessions)} session(s)")
    return ExitCode.SUCCESS


def main(args: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        args: Command line arguments (for testing).

    Returns:
        Exit code.
    """
    parser = create_parser()

    try:
        parsed = parser.parse_args(args)
    except SystemExit as e:
        return e.code if e.code is not None else 1

    # Get session directory
    session_base_dir = get_session_dir()

    # Check for debug from environment
    debug = getattr(parsed, "debug", False) or os.environ.get("ETL_DEBUG", "").lower() == "true"

    if parsed.command == "import":
        # GitHub provider uses URL string, others use Path
        input_arg = parsed.input if parsed.provider == "github" else Path(parsed.input)
        return run_import(
            input_path=input_arg,
            provider=parsed.provider,
            session_id=parsed.session,
            debug=debug,
            dry_run=parsed.dry_run,
            limit=parsed.limit,
            fetch_titles=not parsed.no_fetch_titles,
            chunk=parsed.chunk,
            session_base_dir=session_base_dir,
        )

    elif parsed.command == "organize":
        return run_organize(
            input_path=Path(parsed.input),
            session_id=parsed.session,
            debug=debug,
            dry_run=parsed.dry_run,
            limit=parsed.limit,
            session_base_dir=session_base_dir,
        )

    elif parsed.command == "status":
        return run_status(
            session_id=parsed.session,
            show_all=parsed.all,
            as_json=parsed.json,
            session_base_dir=session_base_dir,
        )

    elif parsed.command == "retry":
        return run_retry(
            session_id=parsed.session,
            phase=parsed.phase,
            debug=debug,
            session_base_dir=session_base_dir,
        )

    elif parsed.command == "clean":
        return run_clean(
            days=parsed.days,
            dry_run=parsed.dry_run,
            force=parsed.force,
            session_base_dir=session_base_dir,
        )

    elif parsed.command == "trace":
        return run_trace(
            session_id=parsed.session,
            target=parsed.target,
            item_id=parsed.item,
            show_content=parsed.show_content,
            session_base_dir=session_base_dir,
        )

    return ExitCode.ERROR


if __name__ == "__main__":
    sys.exit(main())
