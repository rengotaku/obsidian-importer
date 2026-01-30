"""CLI - コマンドライン（引数パーサー、コマンド実装）"""

from normalizer.cli.parser import create_parser
from normalizer.cli.status import cmd_status
from normalizer.cli.metrics import cmd_metrics
from normalizer.cli.commands import main

__all__ = [
    # parser.py
    "create_parser",
    # status.py
    "cmd_status",
    # metrics.py
    "cmd_metrics",
    # commands.py
    "main",
]
