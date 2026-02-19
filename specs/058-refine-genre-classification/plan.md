# Implementation Plan: ETL ジャンル分類の細分化

**Branch**: `058-refine-genre-classification` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/058-refine-genre-classification/spec.md`

## Summary

現在67%を占める「その他」カテゴリを30%以下に削減するため、6つの新ジャンル（ai, devops, lifestyle, parenting, travel, health）を追加し、既存の `classify_genre` 関数を拡張する。キーワードマッチングベースの分類ロジックを維持しつつ、優先順位を設定可能にする。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, PyYAML 6.0+
**Storage**: ファイルシステム (PartitionedDataset)
**Testing**: unittest (標準ライブラリ)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: Single (Kedro パイプライン)
**Performance Goals**: パイプライン実行時間が現状から10%以上増加しない
**Constraints**: LLM不使用（キーワードマッチングのみ）
**Scale/Scope**: 約313件のナレッジファイル

## Constitution Check

*Constitution ファイルが存在しないため、スキップ*

## Project Structure

### Documentation (this feature)

```text
specs/058-refine-genre-classification/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md  # Specification checklist
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipelines/
│   └── organize/
│       ├── nodes.py          # classify_genre 関数を拡張
│       └── pipeline.py
└── ...

conf/base/
└── parameters.yml            # genre_keywords に新ジャンル追加

tests/
├── test_organize_files.py    # 既存テスト更新
└── ...

CLAUDE.md                     # ジャンル説明を更新
```

**Structure Decision**: 既存の Kedro パイプライン構造を維持。`nodes.py` の `classify_genre` 関数を拡張し、`parameters.yml` にキーワードを追加する。

## Implementation Phases

### Phase 1: Setup (Configuration)

| Task | Description | Files |
|------|-------------|-------|
| 1.1 | 新ジャンル用キーワードを parameters.yml に追加 | `conf/base/parameters.yml` |
| 1.2 | ジャンル優先順位リストを parameters.yml に追加 | `conf/base/parameters.yml` |

### Phase 2: Core Implementation

| Task | Description | Files |
|------|-------------|-------|
| 2.1 | classify_genre 関数の優先順位ロジックを設定可能に変更 | `src/obsidian_etl/pipelines/organize/nodes.py` |
| 2.2 | 新ジャンルのサポートを追加 | `src/obsidian_etl/pipelines/organize/nodes.py` |
| 2.3 | ジャンル分布ログ出力機能を追加 | `src/obsidian_etl/pipelines/organize/nodes.py` |

### Phase 3: Testing

| Task | Description | Files |
|------|-------------|-------|
| 3.1 | 新ジャンル分類のユニットテスト追加 | `tests/test_organize_files.py` |
| 3.2 | 既存テストの更新（優先順位変更対応） | `tests/test_organize_files.py` |
| 3.3 | 統合テスト（実データでの検証） | Manual |

### Phase 4: Documentation

| Task | Description | Files |
|------|-------------|-------|
| 4.1 | CLAUDE.md のジャンル説明を更新 | `CLAUDE.md` |

## Complexity Tracking

該当なし（既存パターンの拡張のみ）

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| 既存テストの破損 | 優先順位変更前に既存テストを実行し、影響範囲を特定 |
| キーワード重複 | 新ジャンルキーワードが既存ジャンルと重複しないよう確認 |
| パフォーマンス低下 | ジャンル数増加による影響は軽微（単純なループ追加のみ） |

## Success Validation

1. `make test` - 全テストパス
2. `kedro run` 実行後、`organized/other/` の割合が30%以下
3. ログ出力にジャンル分布が表示される
