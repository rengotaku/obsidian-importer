# Implementation Plan: Scripts コードリファクタリング

**Branch**: `009-scripts-refactor` | **Date**: 2026-01-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-scripts-refactor/spec.md`

## Summary

`ollama_normalizer.py`（3,233行）を論理的なモジュールに分割し、各モジュールを300-500行以内に収める。既存の全機能・CLI互換性を維持しながら、AIおよび開発者がコードを効率的に理解・修正できる構造を実現する。

## Technical Context

**Language/Version**: Python 3.13+ (3.11+ 互換)
**Primary Dependencies**: 標準ライブラリのみ（urllib, json, re, pathlib, argparse, typing）+ `markdown_normalizer.py`（同一ディレクトリ）
**Storage**: ファイルシステム（Obsidian Vault）、JSON状態ファイル
**Testing**: Makefile test-fixtures（手動検証）、構文チェック（py_compile）
**Target Platform**: Linux (Ubuntu)
**Project Type**: Single CLI tool
**Performance Goals**: 既存と同等（LLM API がボトルネック、コード変更による影響なし）
**Constraints**: 標準ライブラリのみ、外部依存禁止
**Scale/Scope**: 単一ファイル（3,233行）→ 18モジュール（各300-500行）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 根拠 |
|------|------|------|
| I. Vault Independence | ✅ Pass | リファクタリングは Vault 構造に影響しない |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力フォーマットは維持、スクリプト内部のみ変更 |
| III. Normalization First | ✅ Pass | 正規化ロジックは維持、構造のみ変更 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類ロジックは維持 |
| V. Automation with Oversight | ✅ Pass | 既存の確認フロー（--preview等）を維持 |

**Gate Status**: ✅ PASSED - 違反なし、Phase 0 進行可

## Project Structure

### Documentation (this feature)

```text
specs/009-scripts-refactor/
├── spec.md              # 機能仕様
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface定義)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py          # エントリポイント（~50行、互換性維持）
├── normalizer/                   # 新規モジュールディレクトリ
│   ├── __init__.py               # パッケージ初期化、公開API
│   ├── config.py                 # 設定値、定数、パス定義（~100行）
│   ├── types.py                  # TypedDict、型定義（~150行）
│   │
│   ├── validators/               # 検証モジュール群
│   │   ├── __init__.py
│   │   ├── title.py              # タイトル検証（~80行）
│   │   ├── tags.py               # タグ検証・正規化（~200行）
│   │   └── format.py             # Markdownフォーマット検証（~100行）
│   │
│   ├── detection/                # 判定モジュール群
│   │   ├── __init__.py
│   │   └── english.py            # 英語文書判定（~100行）
│   │
│   ├── pipeline/                 # LLMパイプライン
│   │   ├── __init__.py
│   │   ├── stages.py             # 各ステージ実装（~400行）
│   │   ├── runner.py             # パイプライン実行（~200行）
│   │   └── prompts.py            # プロンプト管理（~150行）
│   │
│   ├── io/                       # 入出力
│   │   ├── __init__.py
│   │   ├── files.py              # ファイル読み書き（~150行）
│   │   ├── session.py            # セッション管理（~150行）
│   │   └── ollama.py             # Ollama API通信（~150行）
│   │
│   ├── state/                    # 状態管理
│   │   ├── __init__.py
│   │   └── manager.py            # 処理状態管理（~200行）
│   │
│   ├── processing/               # ファイル処理
│   │   ├── __init__.py
│   │   ├── single.py             # 単一ファイル処理（~250行）
│   │   └── batch.py              # バッチ処理（~200行）
│   │
│   ├── output/                   # 出力フォーマット
│   │   ├── __init__.py
│   │   ├── formatters.py         # 結果フォーマット（~150行）
│   │   └── diff.py               # 差分表示（~100行）
│   │
│   └── cli/                      # コマンドライン
│       ├── __init__.py
│       ├── parser.py             # 引数パーサー（~150行）
│       └── commands.py           # コマンド実装（~300行）
│
├── markdown_normalizer.py        # 既存（変更なし）
├── tests/
│   └── fixtures/                 # 既存テストフィクスチャ
└── Makefile                      # 既存（変更なし）
```

**Structure Decision**:
- `.claude/scripts/normalizer/` パッケージとして新規作成
- 既存の `ollama_normalizer.py` はエントリポイントとして維持（インポートのみ）
- 機能別サブパッケージ（validators, detection, pipeline, io, state, processing, output, cli）で責任分離

## Complexity Tracking

> 違反なし - 追跡不要

## Key Technical Decisions (Phase 0 で詳細化)

1. **循環インポート回避**: 型定義を `types.py` に集約、遅延インポート活用
2. **グローバル状態管理**: `_current_session_dir` 等は `state/manager.py` でカプセル化
3. **テスト互換性**: 既存 Makefile ターゲットが動作するよう CLI インターフェース維持
4. **インクリメンタル移行**: モジュールごとに移行・テスト可能な設計

## Next Steps

1. **Phase 0**: `research.md` - 循環インポート回避パターン、Python パッケージベストプラクティス
2. **Phase 1**: `data-model.md` - 型定義の詳細設計
3. **Phase 1**: `contracts/cli.md` - CLI インターフェース仕様
4. **Phase 1**: `quickstart.md` - 開発者向けクイックスタート
