"""Detection - 文書判定モジュール（英語文書判定など）"""

from normalizer.detection.english import (
    count_english_chars,
    count_total_letters,
    is_complete_english_document,
    log_english_detection,
)

__all__ = [
    "count_english_chars",
    "count_total_letters",
    "is_complete_english_document",
    "log_english_detection",
]
