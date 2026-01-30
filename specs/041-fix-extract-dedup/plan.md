# Implementation Plan: 重複処理の解消

**Branch**: `041-fix-extract-dedup` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/041-fix-extract-dedup/spec.md`

## Summary

ChatGPT インポートで N² 重複（1,295 会話 → 1,414,140 レコード）が発生している。根本原因は BaseExtractor テンプレートの不完全さにより、子クラスが責務境界を逸脱していること。

修正方針: **BaseExtractor テンプレートを完成させ、構造的に重複が不可能な設計にする**。具体的には:
1. `_chunk_if_needed()` に `_build_chunk_messages()` hook を追加し、子クラスの override を不要にする
2. ChatGPT Steps から重複処理（ZIP 読み込み・パース・変換）を削除し、バリデーションのみに限定する
3. 全子クラスの冗長な override（`stage_type`, `discover_items()`）を削除する

併せて、入力インターフェースを統一する。**INPUT_TYPE パラメータ（デフォルト: path）と複数 INPUT 対応**を導入し、プロバイダー非依存の入力解決を実現する。

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml: `requires-python = ">=3.11"`)
**Primary Dependencies**: tenacity 8.x（リトライ）、ollama（LLM API）、標準ライブラリ（json, pathlib, dataclasses, zipfile）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）- セッションフォルダ構造
**Testing**: unittest（標準ライブラリ）、`make test` で実行
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project（ETL パイプライン）
**Performance Goals**: 1,295 会話の ChatGPT インポートが重複なく完了すること
**Constraints**: Extract 出力が入力 ZIP サイズの 10 倍以内
**Scale/Scope**: 4 Extractor（Claude, ChatGPT, GitHub, File）+ BaseExtractor フレームワーク + CLI 入力統一

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | N/A | ETL パイプラインコードの変更のみ、Vault 構造に影響なし |
| II. Obsidian Markdown Compliance | N/A | Markdown 出力フォーマットの変更なし |
| III. Normalization First | N/A | 正規化ロジックの変更なし |
| IV. Genre-Based Organization | N/A | ジャンル分類の変更なし |
| V. Automation with Oversight | ✅ PASS | 既存の確認フロー（dry-run 等）を維持 |

**GATE RESULT**: ✅ PASS - 全原則に適合。ETL フレームワーク内部のバグ修正であり、Vault やコンテンツ管理への影響なし。

## Project Structure

### Documentation (this feature)

```text
specs/041-fix-extract-dedup/
├── plan.md              # This file
├── research.md          # Phase 0: 設計方針の調査・決定
├── data-model.md        # Phase 1: エンティティ定義
├── quickstart.md        # Phase 1: 実装ガイド
├── contracts/           # Phase 1: API コントラクト
└── tasks.md             # Phase 2: タスク定義（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── extractor.py       # 【主要変更】BaseExtractor テンプレート完成（_build_chunk_messages hook 追加）
│   └── stage.py           # BaseStage - _max_records_per_file revert
├── stages/extract/
│   ├── chatgpt_extractor.py  # 【主要変更】重複 Steps 削除、_chunk_if_needed override 削除、stage_type 削除
│   ├── claude_extractor.py   # _chunk_if_needed override 削除、stage_type 削除、_build_chunk_messages 実装
│   ├── github_extractor.py   # discover_items override 削除、stage_type 削除
│   └── file_extractor.py     # 回帰確認のみ（BaseStage 系統、変更なし）
├── cli/
│   └── commands/
│       └── import_cmd.py     # INPUT_TYPE + 複数 INPUT 対応
├── phases/
│   └── import_phase.py       # ImportPhase.run() - 入力解決の統一
└── tests/
    ├── test_claude_extractor_refactoring.py
    └── test_github_extractor.py
```

**Structure Decision**: 既存ファイルの修正が中心。入力解決ロジックの新規モジュール追加の可能性あり。

## Complexity Tracking

> No constitution violations. No complexity justification needed.
