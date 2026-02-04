# Implementation Plan: Resume モードでの処理済みアイテムスキップ機能

**Branch**: `033-resume-skip-processed` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/033-resume-skip-processed/spec.md`

## Summary

Resume モード（`--session` オプション）で既存の処理済みアイテムをスキップする機能を追加。Transform Stage での `knowledge_extracted` チェック、入力ファイルコピーのスキップ、統計情報への `skipped_count` 追加により、Resume 実行時間を大幅に削減する。

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml: requires-python = ">=3.11")
**Primary Dependencies**: tenacity 8.x（既存）、ollama（既存）、標準ライブラリ（json, pathlib, dataclasses）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project（CLI ツール）
**Performance Goals**: 処理済みアイテムのスキップ時間 10ms 未満/アイテム
**Constraints**: 後方互換性維持（新規セッションの動作は変更なし）
**Scale/Scope**: 1,000件以上の会話インポートを想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | ETL パイプライン内部の変更、Vault には影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力形式に変更なし |
| III. Normalization First | ✅ Pass | 正規化フローに変更なし |
| IV. Genre-Based Organization | ✅ Pass | 振り分けロジックに変更なし |
| V. Automation with Oversight | ✅ Pass | スキップ理由をログに明示出力 |

## Project Structure

### Documentation (this feature)

```text
specs/033-resume-skip-processed/
├── spec.md              # Feature specification
├── plan.md              # This file
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/etl/
├── cli.py                          # FR3: Resume 時の入力コピースキップ
├── core/
│   ├── session.py                  # FR5: PhaseStats.skipped_count 追加
│   ├── stage.py                    # スキップカウント集計サポート
│   └── status.py                   # ItemStatus.SKIPPED（既存）
├── phases/
│   └── import_phase.py             # FR4: skipped_count 集計・出力
└── stages/
    ├── transform/
    │   └── knowledge_transformer.py # FR1: 処理済みスキップ
    └── load/
        └── session_loader.py        # FR2: ファイル存在チェック

tests/
└── unit/
    └── etl/
        ├── test_resume_skip.py      # 新規: スキップ機能テスト
        └── stages/
            └── transform/
                └── test_knowledge_transformer.py  # 既存テスト拡張
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。変更は `src/etl/` 内の 5 ファイルに限定。

## Technical Research Summary (Phase 0)

### 現状のコード分析

| 箇所 | ファイル:行 | 問題点 |
|------|-------------|--------|
| Resume 入力コピー | `cli.py:285-306` | 毎回 `shutil.copy` で上書き |
| Transform スキップ | `knowledge_transformer.py:139-219` | `knowledge_extracted` チェックなし |
| Load スキップ | `session_loader.py:36-84` | `ItemStatus.SKIPPED` チェックはあるが Transform で設定されない |
| 統計情報 | `session.py:15-69` | `skipped_count` フィールドなし |

### 修正箇所の詳細

#### FR1: ExtractKnowledgeStep.process() 修正

```python
# 追加位置: knowledge_transformer.py:139 付近
def process(self, item: ProcessingItem) -> ProcessingItem:
    # [NEW] 処理済みチェック - Resume スキップ
    if item.metadata.get("knowledge_extracted") is True:
        if item.metadata.get("knowledge_document") is not None:
            item.status = ItemStatus.SKIPPED
            item.metadata["skipped_reason"] = "already_processed"
            return item
    # ... 既存処理
```

#### FR2: WriteToSessionStep.process() 修正

```python
# 追加位置: session_loader.py:36 付近
def process(self, item: ProcessingItem) -> ProcessingItem:
    # [EXISTING] Already handles ItemStatus.SKIPPED from Transform
    if item.status == ItemStatus.SKIPPED:
        item.metadata["skipped"] = True
        item.metadata["skip_reason"] = item.metadata.get("skipped_reason", "skipped in earlier stage")
        return item
    # ... 既存処理
```

#### FR3: cli.py Resume 入力コピースキップ

```python
# 修正位置: cli.py:285 付近
# Resume 時は入力ファイルコピーをスキップ
if not session_id:  # 新規セッションのみコピー
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        shutil.copy(source_path, extract_input)
    else:
        # ... 既存のコピー処理
```

#### FR5: PhaseStats.skipped_count 追加

```python
# 修正位置: session.py:15 付近
@dataclass
class PhaseStats:
    status: str
    success_count: int
    error_count: int
    skipped_count: int = 0  # [NEW]
    completed_at: str
    error: str | None = None
```

## Data Model Changes

### PhaseStats 拡張

| フィールド | 型 | 説明 | 変更 |
|----------|-----|------|------|
| `status` | str | Phase completion status | 既存 |
| `success_count` | int | 成功アイテム数 | 既存 |
| `error_count` | int | 失敗アイテム数 | 既存 |
| `skipped_count` | int | スキップアイテム数 | **新規** |
| `completed_at` | str | 完了日時 | 既存 |
| `error` | str \| None | エラーメッセージ | 既存 |

### ProcessingItem.metadata 拡張

| フィールド | 型 | 説明 | 変更 |
|----------|-----|------|------|
| `knowledge_extracted` | bool | 知識抽出完了フラグ | 既存（読み取り対象に） |
| `knowledge_document` | dict | 抽出済みドキュメント | 既存（読み取り対象に） |
| `skipped_reason` | str | スキップ理由 | **新規** |

## API Contracts

### StageResult (internal)

```python
@dataclass
class StageResult:
    """Stage execution result with skip tracking."""
    success_count: int
    error_count: int
    skipped_count: int  # NEW
```

### CLI Output Format

```
[Session] 20260124_123456 (reused)
[Phase] import started (provider: claude)
[Phase] import completed (100 success, 0 failed, 500 skipped)
```

## Backward Compatibility

| シナリオ | 動作 |
|---------|------|
| 新規セッション（`--session` なし） | 既存と同一（入力コピー、全件処理） |
| 既存セッション Resume | 処理済みスキップ、入力コピーなし |
| 古い session.json 読み込み | `skipped_count=0` でデフォルト |
| debug モードとの組み合わせ | スキップも `steps.jsonl` に記録 |

## Testing Strategy

### Unit Tests

| テスト | 内容 |
|--------|------|
| `test_skip_already_processed` | `knowledge_extracted=True` でスキップ |
| `test_process_without_metadata` | メタデータなしで通常処理 |
| `test_phase_stats_skipped_count` | `skipped_count` シリアライズ |
| `test_cli_resume_no_copy` | Resume 時の入力コピースキップ |

### Integration Tests

| テスト | 内容 |
|--------|------|
| `test_resume_session_e2e` | 部分処理済みセッションの Resume |
| `test_full_skip_session` | 全件処理済みセッションの Resume |

## Complexity Tracking

> 本機能は Constitution Check に違反しないため、この表は空。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | - | - |
