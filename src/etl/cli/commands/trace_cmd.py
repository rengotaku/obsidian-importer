"""Trace command for ETL pipeline.

Traces item processing through pipeline steps for debugging.

Example:
    python -m src.etl trace --session 20260126_140000 --target ALL --item conversation_id
    python -m src.etl trace --session 20260126_140000 --target ERROR --show-error-details
"""

import argparse
import json
import sys
from pathlib import Path

from src.etl.cli.common import ExitCode, get_session_dir
from src.etl.core.session import SessionManager


def register(subparsers) -> None:
    """Register trace command with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object from main parser
    """
    parser = subparsers.add_parser(
        "trace",
        help="Trace item processing through pipeline steps",
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session ID to trace",
    )
    parser.add_argument(
        "--target",
        choices=["ALL", "ERROR"],
        default="ALL",
        help="Target items to trace (default: ALL)",
    )
    parser.add_argument(
        "--item",
        help="Item ID to trace (required when target=ALL)",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show content diffs between steps",
    )
    parser.add_argument(
        "--show-error-details",
        action="store_true",
        help="Show error details (backtrace, metadata) from error_details.jsonl",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute trace command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    session_id = args.session
    target = args.target
    item_id = args.item
    show_content = args.show_content
    show_error_details = args.show_error_details
    session_base_dir = get_session_dir()

    manager = SessionManager(session_base_dir)

    if not manager.exists(session_id):
        print(f"[Error] Session not found: {session_id}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND

    session_path = session_base_dir / session_id

    # Collect error items if target=ERROR
    if target == "ERROR":
        error_items = []

        # Search error_details.jsonl in all phases (more accurate than pipeline_stages.jsonl)
        for phase_dir in session_path.iterdir():
            if not phase_dir.is_dir():
                continue

            error_jsonl = phase_dir / "error_details.jsonl"
            if not error_jsonl.exists():
                continue

            # Read JSONL and collect error item_ids
            try:
                with open(error_jsonl, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        item_id = record.get("item_id")
                        if item_id and item_id not in error_items:
                            error_items.append(item_id)
            except Exception as e:
                print(
                    f"[Warning] Failed to read {error_jsonl}: {e}",
                    file=sys.stderr,
                )

        # Fallback to pipeline_stages.jsonl if no error_details found
        if not error_items:
            print(
                "[Warning] No error_details.jsonl found. Falling back to pipeline_stages.jsonl",
                file=sys.stderr,
            )
            print("[Hint] Run session with --debug to get detailed error tracking", file=sys.stderr)

            for phase_dir in session_path.iterdir():
                if not phase_dir.is_dir():
                    continue

                pipeline_jsonl = phase_dir / "pipeline_stages.jsonl"
                if not pipeline_jsonl.exists():
                    continue

                try:
                    with open(pipeline_jsonl, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            record = json.loads(line)
                            if record.get("status") == "failed":
                                # Try to extract item_id from filename
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

            # Show error details if requested
            if show_error_details:
                print()
                _show_error_details(session_path, error_item_id)

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

        # Show error details if requested
        if show_error_details:
            print()
            _show_error_details(session_path, item_id)

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

        # Look for steps.jsonl in each stage folder
        for stage_dir in phase_dir.iterdir():
            if not stage_dir.is_dir():
                continue

            steps_jsonl = stage_dir / "steps.jsonl"
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


def _show_error_details(
    session_path: Path,
    item_id: str,
) -> None:
    """Show error details from error_details.jsonl.

    Args:
        session_path: Path to session directory.
        item_id: Item ID to show error details for.
    """
    # Search for error_details.jsonl in all phases
    error_records = []

    for phase_dir in session_path.iterdir():
        if not phase_dir.is_dir():
            continue

        error_jsonl = phase_dir / "error_details.jsonl"
        if not error_jsonl.exists():
            continue

        # Read JSONL file
        try:
            with open(error_jsonl, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if record.get("item_id") == item_id:
                        error_records.append(record)
        except Exception as e:
            print(f"[Warning] Failed to read {error_jsonl}: {e}", file=sys.stderr)

    if not error_records:
        print("[Info] No error details found for this item")
        return

    # Display error details
    print("=" * 80)
    print("Error Details:")
    print("=" * 80)

    for idx, record in enumerate(error_records, 1):
        if len(error_records) > 1:
            print(f"\n--- Error {idx}/{len(error_records)} ---")

        # Basic info
        print(f"Timestamp: {record.get('timestamp', 'N/A')}")
        print(f"Stage: {record.get('stage', 'N/A')}")
        print(f"Step: {record.get('step', 'N/A')}")
        print(f"Error Type: {record.get('error_type', 'N/A')}")
        print(f"Error Message: {record.get('error_message', 'N/A')}")

        # Backtrace
        backtrace = record.get("backtrace")
        if backtrace:
            print("\nBacktrace:")
            print("-" * 80)
            # Limit backtrace to last 20 lines for readability
            lines = backtrace.split("\n")
            if len(lines) > 20:
                print("\n".join(lines[:5]))
                print(f"... ({len(lines) - 10} lines omitted) ...")
                print("\n".join(lines[-5:]))
            else:
                print(backtrace)
            print("-" * 80)

        # Metadata
        metadata = record.get("metadata", {})
        if metadata:
            print("\nMetadata:")
            print("-" * 80)

            # Conversation title
            conv_title = metadata.get("conversation_title")
            if conv_title:
                print(f"Conversation Title: {conv_title}")

            # LLM prompt (truncate if too long)
            llm_prompt = metadata.get("llm_prompt")
            if llm_prompt:
                print("\nLLM Prompt:")
                if len(llm_prompt) > 500:
                    print(llm_prompt[:500])
                    print(f"... (truncated, total {len(llm_prompt)} chars)")
                else:
                    print(llm_prompt)

            # LLM output (truncate if too long)
            llm_output = metadata.get("llm_output")
            if llm_output:
                print("\nLLM Output:")
                if len(llm_output) > 500:
                    print(llm_output[:500])
                    print(f"... (truncated, total {len(llm_output)} chars)")
                else:
                    print(llm_output)

            # Other metadata
            for key, value in metadata.items():
                if key not in ["conversation_title", "llm_prompt", "llm_output"]:
                    print(f"{key}: {value}")

            print("-" * 80)
