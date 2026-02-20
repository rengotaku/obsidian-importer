# Implementation Plan: Organize パイプラインの Obsidian Vault 直接出力対応

**Branch**: `059-organize-vault-output` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/059-organize-vault-output/spec.md`

## Summary

organized フォルダ (`data/07_model_output/organized/`) から Obsidian Vault への直接コピー機能を実装する。genre に基づく Vault マッピング、topic によるサブフォルダ配置、競合検出・処理オプション（skip/overwrite/increment）を提供する。Preview モードと実行モードの 2 つの独立パイプラインとして実装。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, PyYAML 6.0+
**Storage**: ファイルシステム (PartitionedDataset for input, 直接ファイルコピー for output)
**Testing**: unittest (標準ライブラリ)
**Target Platform**: Linux (local)
**Project Type**: Single project (Kedro pipeline)
**Performance Goals**: 100 件のファイルを 10 秒以内に処理
**Constraints**: Vault ベースパスが存在すること、frontmatter に genre/topic が存在すること
**Scale/Scope**: 数百件のファイルを想定

## Constitution Check

*GATE: Constitution 未定義のため N/A*

## Project Structure

### Documentation (this feature)

```text
specs/059-organize-vault-output/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipelines/
│   └── vault_output/           # NEW: Vault output pipeline
│       ├── __init__.py
│       ├── pipeline.py         # organize_preview, organize_to_vault pipelines
│       └── nodes.py            # resolve_vault_destination, check_conflicts, copy_to_vault
└── pipeline_registry.py        # Update: register new pipelines

conf/base/
└── parameters.yml              # Update: add vault_base_path, genre_vault_mapping

tests/
└── unit/
    └── pipelines/
        └── vault_output/       # NEW: Unit tests
            ├── __init__.py
            └── test_nodes.py
```

**Structure Decision**: 既存の `pipelines/organize/` と並列に `pipelines/vault_output/` を新規作成。Vault への出力は organize とは独立した関心事のため分離。

## Complexity Tracking

該当なし（Constitution 未定義）
