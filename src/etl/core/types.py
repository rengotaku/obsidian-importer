"""Type enums for ETL pipeline.

Defines PhaseType and StageType for pipeline structure.
"""

from enum import Enum


class PhaseType(Enum):
    """Phase type in ETL pipeline."""

    IMPORT = "import"
    ORGANIZE = "organize"


class StageType(Enum):
    """Stage type in ETL pipeline (ETL pattern)."""

    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
