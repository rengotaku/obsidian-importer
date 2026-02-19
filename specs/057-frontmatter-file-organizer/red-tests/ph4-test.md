# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - User Story 3 入出力パス指定
- FAIL テスト数: 4
- テストファイル: tests/test_organize_files.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_organize_files.py | test_resolve_paths_defaults | config のデフォルトパスが Path として返される |
| tests/test_organize_files.py | test_resolve_paths_custom_input | カスタム input パスが config デフォルトより優先される |
| tests/test_organize_files.py | test_resolve_paths_custom_output | カスタム output パスが config デフォルトより優先される |
| tests/test_organize_files.py | test_resolve_paths_expand_tilde | ~ がホームディレクトリに展開される |

## 実装ヒント
- `scripts/organize_files.py` に `resolve_paths(config: dict, input_path: str | None, output_path: str | None) -> tuple[Path, Path]` を実装
- input_path/output_path が None の場合、config の default_input/default_output を使用
- パスに `~` が含まれる場合は `Path.expanduser()` で展開
- 戻り値は `(Path, Path)` のタプル

## FAIL 出力例
```
ERROR: test_resolve_paths_defaults (tests.test_organize_files.TestResolvePaths.test_resolve_paths_defaults)
引数なしの場合、config のデフォルトパスが使用されること.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/test_organize_files.py", line 552, in setUp
    from scripts.organize_files import resolve_paths
ImportError: cannot import name 'resolve_paths' from 'scripts.organize_files'
```
