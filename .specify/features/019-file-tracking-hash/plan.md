# Implementation Plan: ファイル追跡ハッシュID

**Branch**: `019-file-tracking-hash` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-file-tracking-hash/spec.md`

## Summary

ファイル処理時にコンテンツ+初回パスからハッシュIDを生成し、`processed.json`/`errors.json`に`file_id`フィールドを追加することで、ファイル名変更後も追跡可能にする。既存の`ProcessingResult`型と`update_state`関数を拡張する最小限の変更。

## Technical Context

**Language/Version**: Python 3.11+（既存プロジェクト準拠）
**Primary Dependencies**: 標準ライブラリのみ（hashlib, pathlib）
**Storage**: JSON状態ファイル（`.staging/@plan/`配下）
**Testing**: unittest（既存テストフレームワーク）
**Target Platform**: Linux/macOS（ローカル開発環境）
**Project Type**: single（既存normalizerパッケージへの拡張）
**Performance Goals**: ファイルID生成 < 10ms/file
**Constraints**: 既存ProcessingResult型との後方互換性維持
**Scale/Scope**: 単一セッション内の追跡（1000ファイル程度）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | ログファイルのみ変更、Markdownファイル形式に影響なし |
| III. Normalization First | ✅ Pass | 正規化処理の追跡を改善 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ Pass | 追跡機能追加、自動化の透明性向上 |

**Result**: 全ゲートパス、Phase 0 進行可

## Project Structure

### Documentation (this feature)

```text
specs/019-file-tracking-hash/
├── spec.md              # 仕様書
├── plan.md              # 本ファイル
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (なし - 内部API拡張のみ)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
development/scripts/normalizer/
├── models.py            # ProcessingResult に file_id 追加
├── state/
│   └── manager.py       # update_state に file_id 連携追加
├── processing/
│   └── single.py        # process_single_file でハッシュID生成
└── tests/
    └── test_file_id.py  # 新規テスト
```

**Structure Decision**: 既存normalizerパッケージへの最小限の拡張。新規モジュール不要。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

なし - 全ゲートパス
