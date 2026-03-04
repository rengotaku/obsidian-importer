# Phase 3 RED Tests: User Story 2 - 既存データの移行

**Date**: 2026-03-03
**Status**: RED (FAIL verified)
**User Story**: US2 - 既存データの移行

## Summary

| Item | Value |
|------|-------|
| Tests Created | 20 |
| Failed Count | 20 (ImportError) |
| Test Files | tests/unit/test_migrate_data_layers.py |

## Failed Tests

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/unit/test_migrate_data_layers.py | TestMigrateNoFiles::test_no_files_returns_zero_migrated | 移行元にファイルなし -> migrated=0 |
| tests/unit/test_migrate_data_layers.py | TestMigrateNoFiles::test_no_files_returns_zero_skipped | 移行元にファイルなし -> skipped=0 |
| tests/unit/test_migrate_data_layers.py | TestMigrateNoFiles::test_no_files_returns_empty_errors | 移行元にファイルなし -> errors=[] |
| tests/unit/test_migrate_data_layers.py | TestMigrateNoFiles::test_source_dir_not_exist_returns_zero | 移行元ディレクトリ不在 -> 正常終了 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_single_json_file_migrated | 1 JSON -> 移行先に移動 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_source_file_removed_after_migration | 移行後ソース削除 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_multiple_subdirs_migrated | 複数サブディレクトリ移行 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_json_content_preserved_after_migration | JSON 内容保持 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_md_files_not_migrated | MD ファイル非移行 |
| tests/unit/test_migrate_data_layers.py | TestMigrateJsonFiles::test_target_dir_created_automatically | 移行先ディレクトリ自動作成 |
| tests/unit/test_migrate_data_layers.py | TestMigrateSkipExisting::test_existing_file_skipped | 既存ファイルスキップ |
| tests/unit/test_migrate_data_layers.py | TestMigrateSkipExisting::test_existing_file_not_overwritten | 既存ファイル上書き防止 |
| tests/unit/test_migrate_data_layers.py | TestMigrateSkipExisting::test_mixed_migrate_and_skip | 移行+スキップ混在カウント |
| tests/unit/test_migrate_data_layers.py | TestMigrationSummary::test_migration_result_has_migrated_count | migrated カウント正確 |
| tests/unit/test_migrate_data_layers.py | TestMigrationSummary::test_migration_result_has_skipped_count | skipped カウント正確 |
| tests/unit/test_migrate_data_layers.py | TestMigrationSummary::test_migration_result_has_total | total = migrated + skipped |
| tests/unit/test_migrate_data_layers.py | TestMigrationSummary::test_migration_result_has_details_per_subdir | サブディレクトリ別詳細 |
| tests/unit/test_migrate_data_layers.py | TestMigrateDryRun::test_dry_run_does_not_move_files | dry-run でファイル不移動 |
| tests/unit/test_migrate_data_layers.py | TestMigrateDryRun::test_dry_run_returns_correct_counts | dry-run でカウント正確 |
| tests/unit/test_migrate_data_layers.py | TestMigrateDryRun::test_dry_run_with_existing_files_counts_skipped | dry-run でスキップカウント正確 |
| tests/unit/test_migrate_data_layers.py | TestMigrateDryRun::test_dry_run_does_not_create_target_dirs | dry-run でディレクトリ不作成 |

## Implementation Hints

- `scripts/migrate_data_layers.py` を新規作成
- `MigrationResult` dataclass: `migrated: int`, `skipped: int`, `errors: list`, `total: int` (property), `details: dict`
- `migrate_json_to_model_input(source_base, target_base, dry_run=False) -> MigrationResult`
- 対象サブディレクトリ: classified, cleaned, normalized, topic_extracted, vault_determined, organized
- `*.json` のみ移行、`*.md` は対象外
- `shutil.move` で移動、既存ファイルはスキップ
- dry-run ではカウントのみ、ファイル操作なし

## make test Output (excerpt)

```
ERROR: tests.unit.test_migrate_data_layers (unittest.loader._FailedTest.tests.unit.test_migrate_data_layers)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.unit.test_migrate_data_layers
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/unit/test_migrate_data_layers.py", line 25, in <module>
    from scripts.migrate_data_layers import MigrationResult, migrate_json_to_model_input
ModuleNotFoundError: No module named 'scripts.migrate_data_layers'

----------------------------------------------------------------------
Ran 550 tests in 0.662s
FAILED (errors=19)
```

Note: 18 of the 19 errors are pre-existing integration test failures unrelated to this feature.
The 1 new error is the expected ImportError from test_migrate_data_layers.py.
