"""
Main entry point for normalizer package.

Usage:
    python -m normalizer [args]
"""
import sys
from normalizer.cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
