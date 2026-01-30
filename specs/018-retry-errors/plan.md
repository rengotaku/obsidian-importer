# Implementation Plan: エラーファイルのリトライ機能

**Branch**: `018-retry-errors` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-retry-errors/spec.md`

## Summary

LLM インポート処理で発生したエラーファイルのみを再処理する `--retry-errors` オプションと `make retry` ターゲットを追加。既存の errors.json から対象ファイルを読み込み、新しいセッションで Phase 2 処理を再実行する。元のセッションは履歴として保持し、トレーサビリティを確保する。

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリのみ）
**Primary Dependencies**: なし（標準ライブラリの json, pathlib, argparse, datetime を使用）
**Storage**: ファイルシステム（`.staging/@plan/import_*` 配下に JSON/ログファイル）
**Testing**: unittest（Python 標準ライブラリ）、`make test` で実行
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（CLI ツール拡張）
**Performance Goals**: リトライ対象特定 1秒以内、21件のリトライが全体再実行の10%未満
**Constraints**: 標準ライブラリのみ、既存の llm_import モジュール構造に従う
**Scale/Scope**: 数十件のエラーファイルを想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | 機能は `.staging/@plan/` 配下で完結、Vault に影響なし |
| II. Obsidian Markdown Compliance | ✅ PASS | 出力は既存の Obsidian 形式を維持 |
| III. Normalization First | ✅ PASS | 正規化フローは既存処理を再利用 |
| IV. Genre-Based Organization | ✅ PASS | 既存の分類ロジックを使用 |
| V. Automation with Oversight | ✅ PASS | プレビューモード（`ACTION=preview`）で事前確認可能 |

**Gate Result**: ✅ ALL PASS - Phase 0 に進行可能

## Project Structure

### Documentation (this feature)

```text
specs/018-retry-errors/
├── spec.md              # 機能仕様
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
development/scripts/llm_import/
├── cli.py               # 変更: --retry-errors, --session, --timeout 引数追加
├── common/
│   ├── session_logger.py  # 変更: source_session 対応、リトライヘッダー出力
│   └── retry.py           # 新規: リトライロジック（セッション検出、エラー読込）
└── tests/
    └── test_retry.py      # 新規: リトライ機能のユニットテスト

Makefile                 # 変更: retry ターゲット追加
```

**Structure Decision**: 既存の llm_import モジュール構造に従い、リトライ専用ロジックを `common/retry.py` に分離。CLI エントリポイント（cli.py）は引数処理と呼び出しのみ。

## Complexity Tracking

> No violations - standard extension of existing module
