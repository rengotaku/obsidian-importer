# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - User Story 5 (競合別名保存)
- FAIL テスト数: 3 (+ 17 existing tests blocked by ImportError)
- テストファイル: tests/unit/pipelines/vault_output/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_nodes.py | test_find_incremented_path_first | file.md 存在時に file_1.md パスを返す |
| test_nodes.py | test_find_incremented_path_second | file.md, file_1.md 存在時に file_2.md パスを返す |
| test_nodes.py | test_copy_to_vault_increment_existing | increment モードで file_1.md に保存、元ファイル保持 |

## 実装ヒント
- `src/obsidian_etl/pipelines/vault_output/nodes.py` に `find_incremented_path(dst: Path) -> Path` を実装
- `copy_to_vault()` に `conflict_handling == "increment"` 分岐を追加
- 既存の `# "increment" mode handled in Phase 5` コメント箇所を実装に置換
- increment 時の status は `"incremented"` を返す
- `log_copy_summary()` に incremented カウントの追加が必要になる可能性あり

## FAIL 出力例
```
ERROR: tests.unit.pipelines.vault_output.test_nodes (unittest.loader._FailedTest.tests.unit.pipelines.vault_output.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.unit.pipelines.vault_output.test_nodes
Traceback (most recent call last):
  File "tests/unit/pipelines/vault_output/test_nodes.py", line 36, in <module>
    from obsidian_etl.pipelines.vault_output.nodes import (
    ...
    )
ImportError: cannot import name 'find_incremented_path' from 'obsidian_etl.pipelines.vault_output.nodes'

Ran 404 tests in 5.606s
FAILED (errors=1)
```
