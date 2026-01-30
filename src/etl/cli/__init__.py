"""CLI module for ETL pipeline.

This module has been refactored from a monolithic cli.py (1284 lines)
into a modular structure:

- main.py: CLI entry point and command registry
- common.py: Shared utilities (ExitCode, get_session_dir)
- commands/: Individual command modules

For backward compatibility, main() and individual run_* functions are re-exported.
"""

import argparse
from pathlib import Path
from typing import Optional

from src.etl.cli.commands import (
    clean_cmd,
    import_cmd,
    organize_cmd,
    retry_cmd,
    session_trace_cmd,
    status_cmd,
    trace_cmd,
)
from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.cli.main import create_parser, main

# Re-export Phase classes for backward compatibility
from src.etl.phases.import_phase import ImportPhase
from src.etl.phases.organize_phase import OrganizePhase


def run_import(
    input_path: Path,
    provider: str = "claude",
    session_id: str | None = None,
    debug: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
    no_fetch_titles: bool = False,
    chunk: bool = False,
    session_base_dir: Path | None = None,
    fetch_titles: bool | None = None,  # Legacy parameter (opposite of no_fetch_titles)
) -> int:
    """Backward-compatible wrapper for import command.

    Args:
        input_path: Path to input file or directory
        provider: Provider type (claude, openai, github)
        session_id: Optional session ID to resume
        debug: Enable debug mode
        dry_run: Preview changes without executing
        limit: Maximum number of items to process
        no_fetch_titles: Skip title fetching (new parameter)
        chunk: Enable chunking for large conversations
        session_base_dir: Base directory for sessions
        fetch_titles: Enable title fetching (legacy parameter, opposite of no_fetch_titles)

    Returns:
        Exit code (0 for success)
    """
    # Handle legacy fetch_titles parameter (opposite logic)
    if fetch_titles is not None:
        no_fetch_titles = not fetch_titles

    # Convert single input_path to list (action="append" expects list)
    input_list = [input_path] if input_path else None

    args = argparse.Namespace(
        input=input_list,
        input_type="path",  # Default to path for backward compatibility
        provider=provider,
        session=session_id,
        debug=debug,
        dry_run=dry_run,
        limit=limit,
        no_fetch_titles=no_fetch_titles,
        chunk=chunk,
        _session_base_dir=session_base_dir,  # Internal: override session base dir for tests
    )
    return import_cmd.execute(args)


def run_organize(
    input_path: Path,
    session_id: str | None = None,
    debug: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
    session_base_dir: Path | None = None,
) -> int:
    """Backward-compatible wrapper for organize command.

    Args:
        input_path: Path to input file or directory
        session_id: Optional session ID to resume
        debug: Enable debug mode
        dry_run: Preview changes without executing
        limit: Maximum number of items to process
        session_base_dir: Base directory for sessions

    Returns:
        Exit code (0 for success)
    """
    args = argparse.Namespace(
        input=input_path,
        session=session_id,
        debug=debug,
        dry_run=dry_run,
        limit=limit,
        _session_base_dir=session_base_dir,  # Internal: override session base dir for tests
    )
    return organize_cmd.execute(args)


def run_status(
    session_id: str | None = None,
    all_sessions: bool = False,
    json_output: bool = False,
    session_base_dir: Path | None = None,
    show_all: bool | None = None,  # Legacy parameter (same as all_sessions)
    as_json: bool | None = None,  # Legacy parameter (same as json_output)
) -> int:
    """Backward-compatible wrapper for status command.

    Args:
        session_id: Optional session ID to show
        all_sessions: Show all sessions (new parameter)
        json_output: Output as JSON (new parameter)
        session_base_dir: Base directory for sessions
        show_all: Show all sessions (legacy parameter, same as all_sessions)
        as_json: Output as JSON (legacy parameter, same as json_output)

    Returns:
        Exit code (0 for success)
    """
    # Handle legacy parameters
    if show_all is not None:
        all_sessions = show_all
    if as_json is not None:
        json_output = as_json

    args = argparse.Namespace(
        session=session_id,
        all=all_sessions,
        json=json_output,
        _session_base_dir=session_base_dir,  # Internal: override session base dir for tests
    )
    return status_cmd.execute(args)


def run_retry(
    session_id: str,
    phase: str | None = None,
    debug: bool = False,
    session_base_dir: Path | None = None,
) -> int:
    """Backward-compatible wrapper for retry command.

    Args:
        session_id: Session ID to retry
        phase: Optional phase type to retry
        debug: Enable debug mode
        session_base_dir: Base directory for sessions

    Returns:
        Exit code (0 for success)
    """
    args = argparse.Namespace(
        session=session_id,
        phase=phase,
        debug=debug,
    )
    return retry_cmd.execute(args)


def run_clean(
    days: int = 7,
    dry_run: bool = False,
    force: bool = False,
    session_base_dir: Path | None = None,
) -> int:
    """Backward-compatible wrapper for clean command.

    Args:
        days: Number of days to keep
        dry_run: Preview changes without executing
        force: Skip confirmation prompt
        session_base_dir: Base directory for sessions

    Returns:
        Exit code (0 for success)
    """
    args = argparse.Namespace(
        days=days,
        dry_run=dry_run,
        force=force,
    )
    return clean_cmd.execute(args)


def run_trace(
    session_id: str,
    target: str = "ALL",
    item_id: str | None = None,
    show_content: bool = False,
    show_error_details: bool = False,
    session_base_dir: Path | None = None,
) -> int:
    """Backward-compatible wrapper for trace command.

    Args:
        session_id: Session ID to trace
        target: Target type (ALL or ERROR)
        item_id: Optional item ID to trace
        show_content: Show content diffs
        show_error_details: Show error details
        session_base_dir: Base directory for sessions

    Returns:
        Exit code (0 for success)
    """
    args = argparse.Namespace(
        session=session_id,
        target=target,
        item=item_id,
        show_content=show_content,
        show_error_details=show_error_details,
    )
    return trace_cmd.execute(args)


def run_session_trace(
    session_id: str,
    json_output: bool = False,
    session_base_dir: Path | None = None,
) -> int:
    """Backward-compatible wrapper for session-trace command.

    Args:
        session_id: Session ID to trace
        json_output: Output as JSON
        session_base_dir: Base directory for sessions

    Returns:
        Exit code (0 for success)
    """
    args = argparse.Namespace(
        session=session_id,
        json=json_output,
        _session_base_dir=session_base_dir,  # Internal: override session base dir for tests
    )
    return session_trace_cmd.execute(args)


__all__ = [
    "main",
    "create_parser",
    "ExitCode",
    "get_session_dir",
    "run_import",
    "run_organize",
    "run_status",
    "run_retry",
    "run_clean",
    "run_trace",
    "run_session_trace",
    "ImportPhase",
    "OrganizePhase",
]
