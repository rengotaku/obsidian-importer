# Implementation Plan: @index フォルダ内再帰的Markdown処理

**Branch**: `006-index-markdown-process` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-index-markdown-process/spec.md`

## Summary

既存の `ollama_normalizer.py` のファイル検出ロジックを拡張し、`@index/` フォルダ以下のサブフォルダ内 Markdown ファイルも再帰的に処理対象とする。隠しファイル/フォルダの除外、処理前プレビュー、処理結果統計の表示機能を追加。

## Technical Context

**Language/Version**: Python 3.11+ (標準ライブラリのみ)
**Primary Dependencies**: なし（標準ライブラリの pathlib, json, re 使用）
**Storage**: ファイルシステム（Obsidian Vault）
**Testing**: pytest（既存テストフレームワーク継続）
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single（既存スクリプト拡張）
**Performance Goals**: 1000ファイルまでのスキャン30秒以内
**Constraints**: 標準ライブラリのみ、既存ロジック（ジャンル判定、正規化）は変更しない
**Scale/Scope**: @index/以下の約100-1000ファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | @index → 各Vaultへの振り分けルールは変更なし |
| II. Obsidian Markdown Compliance | ✅ Pass | 既存の正規化ロジックを継続使用 |
| III. Normalization First | ✅ Pass | 正規化処理は既存実装を使用 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル判定ロジックは変更なし |
| V. Automation with Oversight | ✅ Pass | 処理前プレビュー機能を追加（FR-003） |

**Gate Status**: ✅ PASS - 憲法違反なし

## Project Structure

### Documentation (this feature)

```text
specs/006-index-markdown-process/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py    # 変更対象: ファイル検出ロジック拡張
├── markdown_normalizer.py  # 変更なし: 正規化ロジック
├── tests/
│   └── test_recursive_scan.py  # 新規: 再帰スキャンテスト
└── data/
    └── exclusion_patterns.json  # 新規: 除外パターン設定（オプション）
```

**Structure Decision**: 既存の `.claude/scripts/` 構造を維持し、`ollama_normalizer.py` を拡張。新規ファイル作成は最小限に抑える。

## Complexity Tracking

> 憲法違反なし - このセクションは空

## Implementation Approach

### 変更箇所の特定

1. **ollama_normalizer.py** 内の `INDEX_DIR.glob("*.md")` を `INDEX_DIR.rglob("*.md")` に変更
2. 除外パターンフィルタ関数を追加
3. プレビュー表示機能を追加
4. 処理結果統計表示を強化

### 除外パターン（デフォルト）

- 隠しファイル: `.*`
- 隠しフォルダ: `.*/**`
- Obsidian設定: `.obsidian/**`

### 影響範囲

- `collect_index_files()` 関数（または同等のファイル収集ロジック）
- メイン処理ループの統計カウント
- CLIオプション（プレビューモード追加）
