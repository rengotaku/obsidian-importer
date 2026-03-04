# Implementation Plan: データレイヤー分離（JSON/MD混在解消）

**Branch**: `064-data-layer-separation` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/064-data-layer-separation/spec.md`

## Summary

`data/07_model_output/` に混在する JSON 中間データと MD 最終出力を Kedro のデータレイヤー設計に従って分離する。JSON ファイルは新設の `data/05_model_input/` へ移動し、`07_model_output/` は MD ファイルのみを格納する。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, PyYAML 6.0+
**Storage**: ファイルシステム (Kedro PartitionedDataset)
**Testing**: unittest（標準ライブラリ）、pytest 互換
**Target Platform**: Linux/macOS ローカル開発環境
**Project Type**: Single project (Kedro パイプライン)
**Performance Goals**: パイプライン処理時間 ±5% 以内
**Constraints**: 既存データの 100% 移行保証
**Scale/Scope**: 数千件の JSON/MD ファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Simplicity**: Does this design favor simplicity over complexity?
  - catalog.yml のパス変更のみで実現
  - 新しい抽象化層は不要
  - 標準的な Kedro PartitionedDataset を継続使用

- [x] **Breaking Changes**: Are breaking changes documented and justified?
  - ディレクトリ構造の変更は破壊的だが、設計品質向上のため許容
  - 移行スクリプトで既存データを保護

- [x] **Testing**: Are test requirements clearly defined?
  - 既存テストのパス更新
  - 移行スクリプトの単体テスト
  - E2E テストでパイプライン全体の動作確認
  - 80% カバレッジ維持

- [x] **Code Quality**: Are linting requirements addressed?
  - ruff と pylint チェック必須
  - 型ヒント追加（移行スクリプト）

- [x] **Idempotency**: Are operations designed to be idempotent?
  - パイプラインの冪等性は維持
  - 移行スクリプトも冪等（既存ファイルスキップ）

- [x] **Traceability**: Is data lineage tracked?
  - file_id による追跡は変更なし
  - ディレクトリ変更後も SHA256 ハッシュで一貫性維持

## Project Structure

### Documentation (this feature)

```text
specs/064-data-layer-separation/
├── spec.md              # 仕様書
├── plan.md              # 本ファイル
├── research.md          # Phase 0 リサーチ
├── data-model.md        # Phase 1 データモデル
├── quickstart.md        # Phase 1 クイックスタート
└── tasks.md             # Phase 2 タスク（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── datasets/            # カスタムデータセット
├── nodes/               # パイプラインノード
├── pipelines/           # パイプライン定義
└── utils/
    └── log_context.py   # iter_with_file_id 簡素化対象

conf/base/
└── catalog.yml          # パス更新対象

scripts/
└── migrate_data_layers.py  # 新規: 移行スクリプト

tests/
├── unit/                # 単体テスト
└── integration/         # 統合テスト
```

**Structure Decision**: 既存の Kedro プロジェクト構造を維持。`scripts/` に移行ユーティリティを追加。

## Implementation Phases

### Phase 1: Setup - catalog.yml 更新

**目的**: JSON データセットのパスを `05_model_input/` に変更

**変更対象データセット**:

| データセット名 | 現在のパス | 新パス |
|---------------|-----------|--------|
| classified_items | 07_model_output/classified | 05_model_input/classified |
| existing_classified_items | 07_model_output/classified | 05_model_input/classified |
| topic_extracted_items | 07_model_output/topic_extracted | 05_model_input/topic_extracted |
| normalized_items | 07_model_output/normalized | 05_model_input/normalized |
| cleaned_items | 07_model_output/cleaned | 05_model_input/cleaned |
| vault_determined_items | 07_model_output/vault_determined | 05_model_input/vault_determined |
| organized_items | 07_model_output/organized | 05_model_input/organized |

**維持するデータセット** (07_model_output):
- markdown_notes
- review_notes
- organized_notes
- organized_files

### Phase 2: TDD - 移行スクリプト

**目的**: 既存データを新構造に移行するスクリプトの作成

**テストファースト**:
1. テスト: 移行元にファイルなし → 正常終了、0件移行
2. テスト: JSON ファイル移行 → 新ディレクトリに移動
3. テスト: 既存ファイルスキップ → スキップ数報告
4. テスト: サマリー出力 → 移行/スキップ数表示

**実装**:
```python
# scripts/migrate_data_layers.py
def migrate_json_to_model_input(dry_run: bool = False) -> MigrationResult:
    """07_model_output の JSON を 05_model_input に移行"""
```

### Phase 3: TDD - iter_with_file_id 簡素化

**目的**: dict/str 分岐処理の削除

**現状** (lines 129-174 in log_context.py):
- dict 入力: metadata.file_id または file_id から抽出
- str 入力: frontmatter から file_id 抽出

**変更後**:
- str 入力のみサポート（Markdown パス）
- dict 入力は TypeError を送出

**テストファースト**:
1. テスト: str パス入力 → 正常処理
2. テスト: dict 入力 → TypeError
3. テスト: frontmatter から file_id 抽出

### Phase 4: Polish - テスト・ドキュメント更新

**目的**: 関連ファイルの整合性確保

**更新対象**:
- tests/: パス参照の更新
- CLAUDE.md: ディレクトリ構造説明の更新
- .gitignore: 必要に応じて 05_model_input を追加

## Risk Analysis

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 移行漏れ | 高 | dry-run モードで事前確認 |
| パイプライン破損 | 高 | 段階的な変更とテスト |
| パフォーマンス低下 | 中 | 前後でベンチマーク比較 |

## Complexity Tracking

> 複雑性の正当化は不要。すべて標準的な Kedro パターンに従う。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
