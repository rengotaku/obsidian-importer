"""ZIP file handling utilities for ChatGPT export.

Provides functionality to extract conversations.json from ChatGPT export ZIP files.
"""

import json
import zipfile
from pathlib import Path
from typing import Any


def read_conversations_from_zip(zip_path: Path) -> dict[str, Any]:
    """Read conversations.json from ChatGPT export ZIP file.

    Args:
        zip_path: Path to ChatGPT export ZIP file.

    Returns:
        Parsed JSON data from conversations.json.

    Raises:
        FileNotFoundError: If ZIP file doesn't exist.
        KeyError: If conversations.json not found in ZIP.
        json.JSONDecodeError: If conversations.json is invalid JSON.
        zipfile.BadZipFile: If file is not a valid ZIP.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    # T049: Handle corrupted ZIP (zipfile.BadZipFile will be raised)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Look for conversations.json in the ZIP
            if 'conversations.json' not in zf.namelist():
                raise KeyError(f"conversations.json not found in {zip_path}")

            # Read and parse JSON
            with zf.open('conversations.json') as f:
                data = json.load(f)
    except zipfile.BadZipFile as e:
        raise zipfile.BadZipFile(f"Corrupted ZIP file: {zip_path}") from e

    return data
