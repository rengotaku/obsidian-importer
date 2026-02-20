# Phase 3 RED Tests: US2+US3 Copy to Vault

**Date**: 2026-02-20
**Phase**: テスト実装 (RED)
**Status**: PASSED (tests now GREEN)

## Test Overview

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| TestCopyToVault | test_copy_to_vault_creates_file | ファイルがVaultの正しい位置にコピーされる |
| TestCopyToVault | test_copy_to_vault_creates_subfolder | サブフォルダが自動作成される |
| TestCopyToVault | test_copy_to_vault_skip_existing | 既存ファイルはskipモードでスキップ |
| TestCopyToVault | test_copy_to_vault_permission_error_skips | パーミッションエラーは例外を投げずにerrorステータス |
| TestLogCopySummary | test_log_copy_summary_output_format | コピーサマリーが正しい形式で返される |

## Test File

`tests/unit/pipelines/vault_output/test_nodes.py`

## Target Functions

- `copy_to_vault(organized_files, destinations, params) -> list[dict]`
- `log_copy_summary(copy_results) -> dict`

## RED Phase Result

Initial failure: `ImportError: cannot import name 'copy_to_vault'`

Functions did not exist in nodes.py at the start of Phase 3.

## GREEN Phase Implementation

Functions implemented in `src/obsidian_etl/pipelines/vault_output/nodes.py`:
- `copy_to_vault()`: File copy with conflict handling
- `log_copy_summary()`: Copy results summary

Pipeline created in `pipeline.py`:
- `create_vault_pipeline()`: organize_to_vault pipeline

Registered in `pipeline_registry.py`:
- `organize_to_vault` pipeline
