"""Module entry point for ETL pipeline.

Enables running via: python -m src.etl [command] [options]
"""

import sys

from src.etl.cli import main

if __name__ == "__main__":
    sys.exit(main())
