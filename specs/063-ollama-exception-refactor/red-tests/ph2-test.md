# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1 - エラー発生時のファイル特定
- FAIL テスト数: 19 メソッド (36 errors including tearDown)
- テストファイル: tests/utils/test_log_context.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/utils/test_log_context.py | test_set_file_id_basic | set_file_id で設定した値が get_file_id で取得できる |
| tests/utils/test_log_context.py | test_set_file_id_overwrite | 複数回呼ぶと最後の値が有効 |
| tests/utils/test_log_context.py | test_set_file_id_with_sha256_prefix | 12文字 SHA256 プレフィックスで正常動作 |
| tests/utils/test_log_context.py | test_set_file_id_with_unicode | Unicode file_id で正常動作 |
| tests/utils/test_log_context.py | test_get_file_id_default | 未設定時のデフォルトは空文字列 |
| tests/utils/test_log_context.py | test_get_file_id_after_set | set 後に正しい値が取得できる |
| tests/utils/test_log_context.py | test_clear_file_id_resets_to_default | clear 後にデフォルト値に戻る |
| tests/utils/test_log_context.py | test_clear_file_id_when_already_empty | 未設定状態で clear してもエラーにならない |
| tests/utils/test_log_context.py | test_set_clear_set_cycle | set/clear/set サイクルが正常動作 |
| tests/utils/test_log_context.py | test_format_with_file_id_prepends_prefix | file_id 設定時に [file_id] がメッセージ前に付与 |
| tests/utils/test_log_context.py | test_format_with_file_id_prefix_position | [file_id] がメッセージの先頭に位置 |
| tests/utils/test_log_context.py | test_format_with_file_id_and_full_format | 完全フォーマットでも [file_id] が含まれる |
| tests/utils/test_log_context.py | test_format_warning_level_with_file_id | WARNING レベルでも [file_id] が付与 |
| tests/utils/test_log_context.py | test_format_without_file_id_no_prefix | file_id 未設定時はプレフィックスなし |
| tests/utils/test_log_context.py | test_format_without_file_id_no_empty_brackets | [] や [None] が出力されない |
| tests/utils/test_log_context.py | test_format_after_clear_no_prefix | clear 後はプレフィックスなし |
| tests/utils/test_log_context.py | test_format_without_file_id_preserves_full_format | 未設定時に完全フォーマットが保持 |
| tests/utils/test_log_context.py | test_inherits_from_logging_formatter | logging.Formatter のサブクラス |
| tests/utils/test_log_context.py | test_can_be_used_with_handler | logging.Handler に設定可能 |

## 実装ヒント
- `src/obsidian_etl/utils/log_context.py` に以下を実装:
  - `_file_id_var: ContextVar[str] = ContextVar("file_id", default="")`
  - `set_file_id(file_id: str) -> None`
  - `get_file_id() -> str`
  - `clear_file_id() -> None`
  - `class ContextAwareFormatter(logging.Formatter)` with `format()` override
- ContextAwareFormatter.format() は `get_file_id()` を呼び、空でなければ `[{file_id}] {message}` 形式で record.msg を書き換えてから `super().format(record)` を呼ぶ

## FAIL 出力例
```
ERROR: test_set_file_id_basic (tests.utils.test_log_context.TestSetFileId.test_set_file_id_basic)
set_file_id で設定した値が get_file_id で取得できること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_log_context.py", line 31, in test_set_file_id_basic
    from obsidian_etl.utils.log_context import get_file_id, set_file_id
ModuleNotFoundError: No module named 'obsidian_etl.utils.log_context'
```
