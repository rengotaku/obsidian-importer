# Implementation Plan: Vault配下ファイル階層化

**Branch**: `013-vault-hierarchy` | **Date**: 2026-01-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-vault-hierarchy/spec.md`

## Summary

Vault（エンジニア、ビジネス等）のルート直下に散在する大量のファイル（エンジニアVaultで927件）を、LLMを使ってサブフォルダに自動分類する。既存の`ollama_genre_classifier.py`を拡張し、ジャンル判定とサブフォルダ判定を1回のLLM呼び出しで同時に行う統合型アプローチを採用。

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリ中心）
**Primary Dependencies**: urllib, json, pathlib, csv, argparse（標準ライブラリのみ）
**Storage**: ファイルシステム（Obsidian Vault）、JSON/CSVログ
**Testing**: pytest（既存テストインフラ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（CLIスクリプト）
**Performance Goals**: 1000ファイルあたり10分以内（LLM呼び出しがボトルネック）
**Constraints**: Ollama API依存、オフライン動作不可
**Scale/Scope**: 最大1000ファイル/Vault、5 Vault

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | 各Vault独立で処理、Vault間移動なし |
| II. Obsidian Markdown Compliance | ✅ Pass | `[[]]` リンク形式維持 |
| III. Normalization First | ✅ Pass | `normalized: true` のファイルのみ対象 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル＋サブフォルダ分類 |
| V. Automation with Oversight | ✅ Pass | ドライランデフォルト、確認後実行 |

## Project Structure

### Documentation (this feature)

```text
specs/013-vault-hierarchy/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli-interface.md # CLI仕様
│   └── llm-prompt.md    # LLMプロンプト仕様
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
├── hierarchy_organizer.py    # 新規: メインスクリプト
├── ollama_genre_classifier.py # 既存: 参照（コード再利用）
└── markdown_normalizer.py    # 既存: 参照

@index/
└── hierarchy_logs/           # 新規: 移動ログ保存先
    └── {session_id}.json

Makefile                      # 既存: ターゲット追加
```

**Structure Decision**: 既存の`.claude/scripts/`ディレクトリに新規スクリプト追加。単一プロジェクト構成を維持。

## Complexity Tracking

*No violations identified - simple CLI script addition.*

## Phase Artifacts

### Phase 0: Research
- [x] [research.md](./research.md) - 技術調査完了

### Phase 1: Design
- [x] [data-model.md](./data-model.md) - データモデル定義
- [x] [contracts/cli-interface.md](./contracts/cli-interface.md) - CLIインターフェース
- [x] [contracts/llm-prompt.md](./contracts/llm-prompt.md) - LLMプロンプト仕様
- [x] [quickstart.md](./quickstart.md) - クイックスタートガイド

### Phase 2: Tasks
- [ ] tasks.md - `/speckit.tasks` で生成
