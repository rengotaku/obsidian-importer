# Implementation Plan: Claude Export Knowledge Extraction

**Branch**: `015-claude-export-docs` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-claude-export-docs/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Claude (web) エクスポートデータ（conversations.json）から会話ログを読み込み、ローカル LLM（Ollama）を使用して知識を抽出し、Obsidian 形式のナレッジドキュメントを生成する。既存の `parse_claude_export.py`（Phase 1）と `ollama_normalizer.py`（Phase 3）の間に、新規 Phase 2 スクリプトを追加する。

## Technical Context

**Language/Version**: Python 3.13+ (3.11+ 互換)
**Primary Dependencies**: 標準ライブラリのみ（urllib, json, re, pathlib, argparse）+ Ollama API
**Storage**: Markdown ファイル（@index/claude/parsed/conversations/ → @index/）、JSON 状態ファイル
**Testing**: unittest（`make test` で実行、LLM モック）、`make test-fixtures`（実 LLM 目視確認）
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single（CLI ツール群）
**Performance Goals**: 1 会話あたり 30 秒以内（SC-003）
**Constraints**: Ollama API 利用可能前提、標準ライブラリのみ（外部パッケージ禁止）
**Scale/Scope**: 1回のエクスポートで数百〜数千会話を処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | 出力は @index/ 経由、Phase 3 で適切な Vault に振り分け |
| II. Obsidian Markdown Compliance | ✅ PASS | frontmatter 必須（title, tags, created, normalized）、Wiki-style リンク |
| III. Normalization First | ✅ PASS | Phase 2 で `normalized: false`、Phase 3 で正規化後 `normalized: true` |
| IV. Genre-Based Organization | ✅ PASS | Phase 3 で既存 ollama_normalizer.py により自動分類 |
| V. Automation with Oversight | ✅ PASS | プレビューモード（FR-008）、中間ファイル削除前に処理完了確認 |

**@index/ 管理ルール準拠**:
- Phase 1 出力: `@index/claude/parsed/conversations/`
- Phase 2 出力: `@index/`（正規化待ち）
- Phase 3 で適切な Vault へ移動

## Project Structure

### Documentation (this feature)

```text
specs/015-claude-export-docs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
scripts/
├── llm_import/                         # LLMエクスポートインポーター ★
│   ├── __init__.py
│   ├── base.py                         # 共通インターフェース・基底クラス ★
│   ├── common/                         # 共通処理
│   │   ├── __init__.py
│   │   ├── ollama.py                   # Ollama API（normalizer/io/ollamaを参照）
│   │   ├── knowledge_extractor.py      # 知識抽出ロジック（共通）★
│   │   └── state.py                    # 処理状態管理（共通）★
│   ├── providers/                      # プロバイダー固有実装
│   │   ├── __init__.py
│   │   ├── claude/                     # Claude (web)
│   │   │   ├── __init__.py
│   │   │   ├── parser.py               # Phase 1: JSON→Markdown ★
│   │   │   └── config.py               # Claude固有設定
│   │   └── chatgpt/                    # ChatGPT（将来）
│   │       ├── __init__.py
│   │       ├── parser.py               # ChatGPT用パーサー
│   │       └── config.py
│   ├── prompts/
│   │   ├── knowledge_extraction.txt    # Phase 2用プロンプト（共通）★
│   │   └── providers/                  # プロバイダー固有プロンプト（必要時）
│   ├── cli.py                          # 統合CLIエントリーポイント ★
│   └── tests/
│       ├── __init__.py
│       ├── test_base.py
│       ├── test_knowledge_extractor.py  # LLM モック使用
│       ├── fixtures/
│       │   ├── claude_export_sample.json    # conversations.json サンプル
│       │   ├── claude_conversation_single.json  # 単一会話
│       │   └── expected_output.md           # 期待出力
│       └── providers/
│           ├── test_claude_parser.py
│           └── test_chatgpt_parser.py  # 将来
├── ollama_normalizer.py                # Phase 3: 既存（変更なし）
└── normalizer/                         # 既存normalizerパッケージ

.claude/commands/og/
├── import-claude.md                    # Claudeインポート ★
└── import-chatgpt.md                   # ChatGPTインポート（将来）

@index/
├── llm_exports/                        # LLMエクスポート入力（統一）
│   ├── claude/                         # Claude用
│   │   └── parsed/conversations/
│   └── chatgpt/                        # ChatGPT用（将来）
│       └── parsed/conversations/
└── *.md                                # Phase 2出力（正規化待ち）
```

**Structure Decision**: 将来の拡張性を考慮し `scripts/llm_import/` パッケージとして設計。
- **common/**: Ollama API、知識抽出、状態管理など共通処理
- **providers/**: Claude、ChatGPT等プロバイダー固有のパーサー
- **base.py**: 共通インターフェース（`BaseParser`, `BaseExtractor`）を定義し、新プロバイダー追加時の実装ガイドとする

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations - all Constitution principles are satisfied.*

## Constitution Check (Post-Design)

*Re-evaluation after Phase 1 design completion*

| Principle | Status | Design Verification |
|-----------|--------|---------------------|
| I. Vault Independence | ✅ PASS | data-model.md で `source_conversation` によるトレーサビリティ確保 |
| II. Obsidian Markdown Compliance | ✅ PASS | contracts/cli-interface.md で frontmatter 形式を定義 |
| III. Normalization First | ✅ PASS | `normalized: false` を明示的に設定、Phase 3 連携 |
| IV. Genre-Based Organization | ✅ PASS | 既存 normalizer パイプライン活用で自動分類 |
| V. Automation with Oversight | ✅ PASS | `--preview` オプション、状態ファイルでエラー追跡 |

**Design Artifacts Alignment**:
- `data-model.md`: エンティティ定義が spec の Key Entities と一致
- `contracts/cli-interface.md`: FR-001〜FR-009 の要件をカバー
- `quickstart.md`: 開発者向けガイドで Constitution 準拠を確認可能

## Testing Strategy

### 方針

| 実行方法 | LLM | 用途 |
|----------|-----|------|
| `make test` | モック | 高速ユニットテスト、CI 相当 |
| `make test-fixtures` | 実 API | 目視確認、品質検証 |

### テスト構成

- **フレームワーク**: `unittest`（既存 normalizer と統一）
- **CI**: 考慮しない（ローカル開発環境のみ）
- **fixtures**: Claude エクスポート JSON サンプルを用意

### テストケース

| テスト | 対象 | モック |
|--------|------|--------|
| `test_base.py` | BaseParser, BaseConversation | なし |
| `test_knowledge_extractor.py` | 知識抽出ロジック | Ollama API |
| `test_claude_parser.py` | JSON パース、Markdown 生成 | なし |

### fixtures 構成

```text
scripts/llm_import/tests/fixtures/
├── claude_export_sample.json       # 複数会話を含む conversations.json
├── claude_conversation_single.json # 単一会話（最小テストケース）
└── expected_output.md              # 期待される出力形式
```

### 知識抽出の品質検証

| 検証 | 方法 | 自動化 |
|------|------|--------|
| 構造 | 必須フィールド存在 | ✅ `make test` |
| フォーマット | frontmatter, Markdown | ✅ `make test` |
| 品質 | 目視確認チェックリスト | ❌ `make test-fixtures` |

**目視確認チェックリスト** (`make test-fixtures` 実行時):

| 項目 | 基準 |
|------|------|
| タイトル | 会話内容を適切に要約 |
| 概要 | 目的と成果が1-2段落 |
| 学び | 3-5項目の具体的内容 |
| アクション | 実践可能な項目 |
| 要点理解 | 元会話なしで理解可能 |

**NG判定**: 概要1文のみ、汎用的すぎる学び、コピペ大半、frontmatter欠落

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Plan | `specs/015-claude-export-docs/plan.md` | ✅ Complete |
| Research | `specs/015-claude-export-docs/research.md` | ✅ Complete |
| Data Model | `specs/015-claude-export-docs/data-model.md` | ✅ Complete |
| Contracts | `specs/015-claude-export-docs/contracts/cli-interface.md` | ✅ Complete |
| Quickstart | `specs/015-claude-export-docs/quickstart.md` | ✅ Complete |
| Tasks | `specs/015-claude-export-docs/tasks.md` | ✅ Complete |

## Next Steps

`/speckit.implement` を実行して実装開始:
- Phase 1: Setup (9 tasks)
- Phase 2: Foundational (7 tasks)
- Phase 3: US-1 MVP (12 tasks)
