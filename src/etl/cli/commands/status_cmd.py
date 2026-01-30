"""Status command for ETL pipeline.

Shows session processing status and statistics.

Example:
    python -m src.etl status
    python -m src.etl status --session 20260126_140000
    python -m src.etl status --all --json
"""

import argparse
import json
import sys

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.cli.utils.pipeline_stats import calculate_phase_stats
from src.etl.core.session import SessionManager


def register(subparsers) -> None:
    """Register status command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "status",
        help="Show session status",
    )
    parser.add_argument(
        "--session",
        help="Show specific session",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all sessions",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute status command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    session_id = args.session
    show_all = args.all
    as_json = args.json
    # Allow override for tests via _session_base_dir
    session_base_dir = getattr(args, "_session_base_dir", None) or get_session_dir()

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
            if session.provider:
                print(f"Provider: {session.provider}")

            # Show phase details
            if session.phases:
                print("\nPhases:")
                for phase_name, phase_stats in session.phases.items():
                    # Calculate statistics from pipeline_stages.jsonl
                    phase_dir = session.base_path / phase_name
                    stats = calculate_phase_stats(phase_dir)

                    print(f"  {phase_name}:")
                    print(f"    Status: {phase_stats.status}")
                    print(f"    Success: {stats.success_count}")
                    print(f"    Failed: {stats.error_count}")
                    if stats.skipped_count > 0:
                        print(f"    Skipped: {stats.skipped_count}")
                    if phase_stats.completed_information:
                        print(f"    Completed: {phase_stats.completed_information.completed_at}")
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
                    # Calculate statistics from pipeline_stages.jsonl
                    phase_dir = session.base_path / phase_name
                    stats = calculate_phase_stats(phase_dir)

                    print(f"  {phase_name}:")
                    print(f"    Status: {phase_stats.status}")
                    print(f"    Success: {stats.success_count}")
                    print(f"    Failed: {stats.error_count}")
                    if stats.skipped_count > 0:
                        print(f"    Skipped: {stats.skipped_count}")
                    if phase_stats.completed_information:
                        print(f"    Completed: {phase_stats.completed_information.completed_at}")
                    if phase_stats.error:
                        print(f"    Error: {phase_stats.error}")
            else:
                print("Phases: none")

        return ExitCode.SUCCESS
