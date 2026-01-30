"""Clean command for ETL pipeline.

Cleans old sessions from the session directory.

Example:
    python -m src.etl clean --days 7 --dry-run
    python -m src.etl clean --days 30 --force
"""

import argparse
import shutil
import sys
from datetime import datetime, timedelta

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.core.session import SessionManager


def register(subparsers) -> None:
    """Register clean command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "clean",
        help="Clean old sessions",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Clean sessions older than N days (default: 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without deleting",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute clean command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    days = args.days
    dry_run = args.dry_run
    force = args.force
    session_base_dir = get_session_dir()

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
