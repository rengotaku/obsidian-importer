"""Output - 出力フォーマット（結果表示、差分表示）"""

from normalizer.output.formatters import (
    format_success_result,
    format_dust_result,
    format_error_result,
    format_skip_result,
    output_json_result,
)
from normalizer.output.diff import (
    show_diff,
    process_file_with_diff,
)

__all__ = [
    # formatters.py
    "format_success_result",
    "format_dust_result",
    "format_error_result",
    "format_skip_result",
    "output_json_result",
    # diff.py
    "show_diff",
    "process_file_with_diff",
]
