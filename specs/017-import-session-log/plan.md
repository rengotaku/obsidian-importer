# Implementation Plan: Import Session Log

**Branch**: `017-import-session-log` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/017-import-session-log/spec.md`

## Summary

`llm_import` CLI に `normalizer` と同等のセッション管理機能を追加し、`.staging/@plan/import_YYYYMMDD_HHMMSS/` に進捗ログを出力する。既存の `normalizer/io/session.py` を再利用し、プレフィックス指定機能を追加。コンソール出力をリッチ化（プログレスバー、Phase 別結果、詳細サマリー）し、同内容を `execution.log` にも記録する。

## Technical Context

**Language/Version**: Python 3.11+（既存プロジェクト準拠）
**Primary Dependencies**: 標準ライブラリのみ（json, pathlib, datetime, time）
**Storage**: ファイルシステム（`.staging/@plan/` 配下に JSON/JSONL/テキストログ）
**Testing**: pytest（既存テストフレームワーク）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single（既存 scripts/ 構造を踏襲）
**Performance Goals**: 処理開始から1秒以内にセッションディレクトリ作成
**Constraints**: ログ機能エラー時も本処理は継続（graceful degradation）
**Scale/Scope**: 数百〜数千会話の処理を想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault には影響なし（@plan は管理用） |
| II. Obsidian Markdown Compliance | N/A | Markdown ファイル出力なし |
| III. Normalization First | N/A | ナレッジファイルには影響なし |
| IV. Genre-Based Organization | N/A | 整理機能には影響なし |
| V. Automation with Oversight | ✅ Pass | ログ出力により処理状況を可視化 |

**Result**: 全ゲート Pass

## Project Structure

### Documentation (this feature)

```text
specs/017-import-session-log/
├── spec.md              # 仕様書
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (内部API定義)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
.dev/scripts/
├── normalizer/
│   └── io/
│       └── session.py        # 既存: プレフィックス引数追加
├── llm_import/
│   ├── cli.py                # 変更: セッションログ統合
│   └── common/
│       └── session_logger.py # 新規: セッションログラッパー
└── tests/
    └── llm_import/
        └── test_session_logger.py  # 新規: ユニットテスト
```

**Structure Decision**: 既存の `normalizer/io/session.py` を拡張し、`llm_import/common/session_logger.py` でラップする形で実装。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |

シンプルな設計を維持。既存モジュールの再利用により複雑性を抑制。
