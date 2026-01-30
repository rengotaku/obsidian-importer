"""Import command for ETL pipeline.

Imports conversation data from Claude, ChatGPT, or GitHub exports
and converts them to Obsidian markdown format.

Example:
    python -m src.etl import --input ~/exports/claude --provider claude
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
from src.etl.phases.import_phase import ImportPhase


def register(subparsers) -> None:
    """Register import command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "import",
        help="Import Claude/ChatGPT export data",
    )
    parser.add_argument(
        "--input",
        required=False,
        action="append",
        help="Input source (repeatable). Path or URL depending on --input-type. Not required for Resume mode.",
    )
    parser.add_argument(
        "--input-type",
        default="path",
        choices=["path", "url"],
        help="Input source type (default: path). 'url' for remote sources like GitHub.",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "openai", "github"],
        help="Source provider (required for new sessions, optional for Resume)",
    )
    parser.add_argument(
        "--session",
        help="Reuse existing session ID",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="[DEPRECATED] Debug mode is now always enabled. This flag has no effect.",
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
    parser.add_argument(
        "--no-fetch-titles",
        action="store_true",
        help="Disable URL title fetching (default: enabled)",
    )
    parser.add_argument(
        "--chunk",
        action="store_true",
        help="Enable chunking for large files (>25000 chars). Default: skip with too_large frontmatter",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute import command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    input_list = args.input  # Now a list (action="append")
    input_type = args.input_type
    provider = args.provider
    session_id = args.session
    debug = args.debug
    dry_run = args.dry_run
    limit = args.limit
    fetch_titles = not args.no_fetch_titles
    chunk = args.chunk
    # Allow override for tests via _session_base_dir
    session_base_dir = getattr(args, "_session_base_dir", None) or get_session_dir()

    # FR-012: Debug mode is always enabled
    if debug:
        print(
            "[Warning] --debug flag is deprecated. Debug mode is now always enabled.",
            file=sys.stderr,
        )

    # Validate: INPUT and PROVIDER required for new sessions
    if not session_id and not input_list:
        print("[Error] --input is required for new sessions", file=sys.stderr)
        print("  For Resume mode, use: --session SESSION_ID", file=sys.stderr)
        return ExitCode.ERROR

    if not session_id and not provider:
        print("[Error] --provider is required for new sessions", file=sys.stderr)
        print("  Example: --provider claude|openai|github", file=sys.stderr)
        return ExitCode.ERROR

    # T072: Input validation based on input_type
    if input_list and not session_id:
        for inp in input_list:
            if input_type == "path":
                # Validate path exists
                path = Path(inp) if not isinstance(inp, Path) else inp
                if not path.exists():
                    print(f"[Error] Input path not found: {inp}", file=sys.stderr)
                    return ExitCode.INPUT_NOT_FOUND
            elif input_type == "url":
                # Validate URL format
                if not inp.startswith(("http://", "https://")):
                    print(f"[Error] Invalid URL format: {inp}", file=sys.stderr)
                    return ExitCode.ERROR

    # Resume mode: auto-detect input and provider from session
    if session_id and not input_list:
        manager = SessionManager(session_base_dir)
        if not manager.exists(session_id):
            print(f"[Error] Session not found: {session_id}", file=sys.stderr)
            return ExitCode.INPUT_NOT_FOUND

        session = manager.load(session_id)
        # Record resume time
        session.resumed_at = datetime.now()
        manager.save(session)

        extract_input_dir = session.base_path / "import" / "extract" / "input"

        # Auto-detect provider and input from extract/input/
        if not extract_input_dir.exists():
            print(f"[Error] No input files in session: {session_id}", file=sys.stderr)
            return ExitCode.INPUT_NOT_FOUND

        # Use provider from session if available (preferred)
        if session.provider:
            provider = session.provider
            print(f"[Resume] Using saved provider: {provider}")
        else:
            # Fallback: detect provider from input files (backward compatibility)
            zip_files = list(extract_input_dir.glob("*.zip"))
            json_files = list(extract_input_dir.glob("*.json"))
            # Support both old github_url.txt and new url.txt
            url_files = list(extract_input_dir.glob("url.txt"))
            old_url_files = list(extract_input_dir.glob("github_url.txt"))

            if url_files or old_url_files:
                # GitHub provider (URL input)
                provider = "github"
                url_file = url_files[0] if url_files else old_url_files[0]
                source_path = url_file.read_text(encoding="utf-8").strip().split("\n")[0]
                print("[Resume] Detected provider: github")
            elif zip_files:
                # OpenAI/ChatGPT provider
                provider = "openai"
                source_path = zip_files[0]
                print(f"[Resume] Detected provider: openai ({source_path.name})")
            elif json_files:
                # Claude provider
                provider = "claude"
                source_path = extract_input_dir
                print(f"[Resume] Detected provider: claude ({len(json_files)} files)")
            else:
                print(f"[Error] No input files found in session: {session_id}", file=sys.stderr)
                return ExitCode.INPUT_NOT_FOUND

        # Determine source_path based on provider
        if provider == "github":
            # Support both old github_url.txt and new url.txt
            url_file = extract_input_dir / "url.txt"
            old_url_file = extract_input_dir / "github_url.txt"

            if url_file.exists():
                source_path = url_file.read_text(encoding="utf-8").strip().split("\n")[0]
            elif old_url_file.exists():
                source_path = old_url_file.read_text(encoding="utf-8").strip()
            else:
                print(f"[Error] URL file not found in session: {session_id}", file=sys.stderr)
                return ExitCode.INPUT_NOT_FOUND
        elif provider == "openai":
            zip_files = list(extract_input_dir.glob("*.zip"))
            if zip_files:
                source_path = zip_files[0]
            else:
                print(f"[Error] ZIP file not found in session: {session_id}", file=sys.stderr)
                return ExitCode.INPUT_NOT_FOUND
        else:  # claude
            source_path = extract_input_dir
    else:
        # T074: Remove provider-dependent input handling, use input_type instead
        # For new sessions, we'll process the input list in the copy section below
        # Just store the first input as source_path for backward compatibility
        # (Multiple inputs will be copied in the extract_input section)
        if input_type == "url":
            source_path = input_list[0]  # URL string
        else:
            source_path = Path(input_list[0])  # Path object

    # Create or load session (if not already loaded in Resume mode)
    if "session" not in locals():
        manager = SessionManager(session_base_dir)
        if session_id:
            if not manager.exists(session_id):
                print(f"[Error] Session not found: {session_id}", file=sys.stderr)
                return ExitCode.INPUT_NOT_FOUND
            session = manager.load(session_id)
        else:
            # FR-012: debug_mode is always True
            session = manager.create(debug_mode=True, provider=provider)
            manager.save(session)

    if "manager" not in locals():
        manager = SessionManager(session_base_dir)

    print(f"[Session] {session.session_id} {'(reused)' if session_id else 'created'}")

    if dry_run:
        print("[Dry-run] Preview mode - no changes will be made")
        # Count input files
        if input_type == "url":
            print(f"[Dry-run] URL inputs: {len(input_list) if input_list else 0}")
            for url in input_list or []:
                print(f"  - {url}")
        elif (
            isinstance(source_path, Path)
            and source_path.is_file()
            and source_path.suffix.lower() == ".zip"
        ):
            print(f"[Dry-run] ZIP file inputs: {len(input_list) if input_list else 0}")
            for inp in input_list or []:
                print(f"  - {Path(inp).name}")
        else:
            json_files = list(source_path.glob("*.json")) if isinstance(source_path, Path) else []
            if limit:
                json_files = json_files[:limit]
            print(f"[Dry-run] Found {len(json_files)} JSON files")
        return ExitCode.SUCCESS

    # Create phase
    phase_manager = PhaseManager(session.base_path)
    phase_data = phase_manager.create(PhaseType.IMPORT)

    # T073: Input resolution based on input_type
    extract_input = phase_data.stages[StageType.EXTRACT].input_path

    if not session_id:
        # New session: process input list based on input_type
        if input_type == "url":
            # URL type: save all URLs to url.txt (one per line)
            url_file = extract_input / "url.txt"
            url_file.write_text("\n".join(input_list), encoding="utf-8")
        else:
            # Path type: copy all input files/directories
            for inp in input_list:
                inp_path = Path(inp) if not isinstance(inp, Path) else inp

                if inp_path.is_file() and inp_path.suffix.lower() == ".zip":
                    # ZIP file: copy directly
                    shutil.copy(inp_path, extract_input)
                elif inp_path.is_file():
                    # Single JSON file: copy directly
                    shutil.copy(inp_path, extract_input)
                elif inp_path.is_dir():
                    # Directory: copy JSON files (conversations.json priority)
                    file_count = 0
                    conversations_file = inp_path / "conversations.json"
                    if conversations_file.exists():
                        shutil.copy(conversations_file, extract_input)
                        file_count += 1

                    # Copy other JSON files if limit allows
                    for json_file in inp_path.glob("*.json"):
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
        # FR-012: debug_mode is always True
        result = import_phase.run(phase_data, debug_mode=True, limit=limit, session_manager=manager)

        # Reload session to get the expected_total_item_count that was saved after Extract
        session = manager.load(session.session_id)
        current_phase_stats = session.phases.get("import")
        expected_count = current_phase_stats.expected_total_item_count if current_phase_stats else 0

        # Update session with final phase stats
        completed_info = CompletedInformation(
            success_count=result.items_processed,
            error_count=result.items_failed,
            skipped_count=result.items_skipped,
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
        session.phases["import"] = phase_stats

        if result.status == PhaseStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
        elif result.status == PhaseStatus.PARTIAL:
            session.status = SessionStatus.PARTIAL
        else:
            session.status = SessionStatus.FAILED
        manager.save(session)

        # Save phase status (statistics calculated from pipeline_stages.jsonl)
        phase_data.status = result.status
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
        session.phases["import"] = phase_stats
        session.status = SessionStatus.FAILED
        manager.save(session)

        print(f"[Error] Phase import crashed: {error_msg}", file=sys.stderr)
        return ExitCode.ERROR
