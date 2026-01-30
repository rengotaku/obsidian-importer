"""Main CLI entry point and command registry.

This module orchestrates command discovery, registration, and dispatch.
"""

import argparse
import sys

from src.etl.cli.commands import (
    clean_cmd,
    import_cmd,
    organize_cmd,
    retry_cmd,
    session_trace_cmd,
    status_cmd,
    trace_cmd,
)
from src.etl.cli.common import ExitCode

# Command registry - add new commands here
COMMANDS = [
    import_cmd,
    organize_cmd,
    status_cmd,
    retry_cmd,
    clean_cmd,
    trace_cmd,
    session_trace_cmd,
]


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser.

    Returns:
        Configured ArgumentParser with all commands registered
    """
    parser = argparse.ArgumentParser(
        prog="etl",
        description="ETL Pipeline for Obsidian Knowledge Base",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register all commands
    for command_module in COMMANDS:
        command_module.register(subparsers)

    return parser


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Dispatch to appropriate command
    for command_module in COMMANDS:
        # Extract command name from module (e.g., import_cmd -> import)
        # Handle both underscore and hyphen variants (session_trace_cmd -> session-trace)
        command_name = command_module.__name__.split(".")[-1].replace("_cmd", "").replace("_", "-")
        if args.command == command_name:
            return command_module.execute(args)

    # Should never reach here (argparse validates command)
    print(f"[Error] Unknown command: {args.command}", file=sys.stderr)
    return ExitCode.ERROR


if __name__ == "__main__":
    sys.exit(main())
