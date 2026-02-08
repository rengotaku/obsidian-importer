"""BinaryDataset: Kedro AbstractDataset for raw binary files (e.g. ZIP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset


class BinaryDataset(AbstractDataset[bytes, bytes]):
    """Read and write raw binary files.

    Used with PartitionedDataset to load ZIP files as bytes
    without any parsing or encoding conversion.
    """

    def __init__(self, filepath: str) -> None:
        self._filepath = Path(filepath)

    def _load(self) -> bytes:
        return self._filepath.read_bytes()

    def _save(self, data: bytes) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._filepath.write_bytes(data)

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._filepath)}
