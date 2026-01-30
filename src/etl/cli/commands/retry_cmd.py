"""Retry command for ETL pipeline.

Retries failed items in a session.

Example:
    python -m src.etl retry --session 20260126_140000
    python -m src.etl retry --session 20260126_140000 --phase import
"""

import argparse
import sys

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.cli.utils.pipeline_stats import has_failed_items
from src.etl.core.phase import PhaseManager
from src.etl.core.session import SessionManager, SessionStatus
from src.etl.core.types import PhaseType
from src.etl.phases.import_phase import ImportPhase
from src.etl.phases.organize_phase import OrganizePhase


def register(subparsers) -> None:
    """Register retry command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "retry",
        help="Retry failed items",
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session to retry",
    )
    parser.add_argument(
        "--phase",
        choices=["import", "organize"],
        help="Retry specific phase",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute retry command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    session_id = args.session
    phase = args.phase
    debug = args.debug
    session_base_dir = get_session_dir()

    manager = SessionManager(session_base_dir)

    if not manager.exists(session_id):
        print(f"[Error] Session not found: {session_id}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND

    session = manager.load(session_id)
    phase_manager = PhaseManager(session.base_path)

    # Find phases with errors (check pipeline_stages.jsonl)
    phases_to_retry = []

    if phase:
        phase_type = PhaseType(phase)
        if phase_manager.exists(phase_type):
            phase_dir = session.base_path / phase_type.value
            if has_failed_items(phase_dir):
                phases_to_retry.append(phase_type)
    else:
        # Check all phases
        for phase_type in PhaseType:
            if phase_manager.exists(phase_type):
                phase_dir = session.base_path / phase_type.value
                if has_failed_items(phase_dir):
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

        # Update phase status (statistics calculated from pipeline_stages.jsonl)
        phase_data.status = result.status
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
