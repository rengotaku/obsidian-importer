# Implementation Plan: LLMインポート エラーデバッグ改善

**Branch**: `021-import-error-debug` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/021-import-error-debug/spec.md`

## Summary

LLMインポート処理のデバッグ性向上のため、エラー発生時の詳細ファイル出力と中間ファイル保持機能を追加する。また `@plan` フォルダを `organize/`, `import/`, `test/` のサブフォルダに整理し、セッションごとに全処理成果物を集約する。

## Technical Context

**Language/Version**: Python 3.11+（既存プロジェクト準拠）
**Primary Dependencies**: 標準ライブラリのみ（pathlib, json, shutil, datetime）
**Storage**: ファイルシステム（`.staging/@plan/` 配下）
**Testing**: unittest（既存テストフレームワーク）
**Target Platform**: Linux (Ubuntu)
**Project Type**: single（CLIスクリプト）
**Performance Goals**: 既存処理速度を維持
**Constraints**: 追加ディスク使用量は中間ファイル分のみ（10MB上限/エラーファイル）
**Scale/Scope**: 400+会話/セッション

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | @plan は Vault 外、影響なし |
| II. Obsidian Markdown Compliance | ✅ PASS | エラーファイルは Markdown 形式で出力 |
| III. Normalization First | N/A | 正規化対象外（ログファイル） |
| IV. Genre-Based Organization | ✅ PASS | @plan は Vault 振り分け対象外 |
| V. Automation with Oversight | ✅ PASS | 中間ファイルは保持（手動削除） |

## Project Structure

### Documentation (this feature)

```text
specs/021-import-error-debug/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
development/scripts/
├── llm_import/
│   ├── cli.py                    # 修正: セッションフォルダ構造変更
│   ├── common/
│   │   ├── session_logger.py     # 修正: 新フォルダ構造対応
│   │   ├── error_writer.py       # 新規: エラー詳細ファイル出力
│   │   └── folder_manager.py     # 新規: @plan フォルダ管理
│   └── tests/
│       ├── test_error_writer.py  # 新規
│       └── test_folder_manager.py # 新規
└── plan_cleanup.py               # 新規: @plan クリーンアップCLI

.staging/@plan/
├── organize/                     # /og:organize 処理ログ
│   └── {session_id}/
├── import/                       # /og:import-claude 処理ログ
│   └── {session_id}/
│       ├── parsed/conversations/ # Phase 1 出力
│       ├── output/               # Phase 2 出力（@index移動前）
│       ├── errors/               # エラー詳細
│       └── session.json
└── test/                         # テスト実行ログ
    └── {session_id}/
```

**Structure Decision**: 既存の `llm_import/` モジュール構造を維持し、`common/` に新規ユーティリティを追加。

## Complexity Tracking

> No constitution violations requiring justification.
