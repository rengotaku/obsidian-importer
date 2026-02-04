"""Common test fixtures for obsidian-etl tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src directory is on the path for imports
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
