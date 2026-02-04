# Implementation Plan: Summary 日本語化

**Branch**: `008-japanese-summary` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-japanese-summary/spec.md`

## Summary

Claude エクスポート由来ファイルの英語 Summary/Conversation Overview セクションを日本語に翻訳する機能。既存の `stage3_normalize` プロンプトを拡張して実装する。

## Technical Context

**Language/Version**: Python 3.11+（既存スクリプト）
**Primary Dependencies**: Ollama API（既存）、標準ライブラリ
**Storage**: ファイルシステム（Markdown）
**Testing**: 手動テスト + サンプルファイル
**Target Platform**: Linux（ローカル）
**Project Type**: Single project - 既存スクリプトの修正
**Performance Goals**: 処理時間 20% 増加以内（SC-003）
**Constraints**: 翻訳エラー時も処理継続（FR-005）
**Scale/Scope**: 既存の @index/ 処理フローに統合

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault 構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | Markdown 形式は保持 |
| III. Normalization First | ✅ Pass | 正規化プロセスの拡張 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ Pass | 既存の確認フロー維持 |

**Gate Result**: ✅ PASS - 全原則に準拠

## Project Structure

### Documentation (this feature)

```text
specs/008-japanese-summary/
├── spec.md              # 仕様書
├── plan.md              # This file
├── research.md          # Phase 0 output
└── checklists/
    └── requirements.md  # 品質チェックリスト
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py    # 修正不要（プロンプト参照のみ）
└── prompts/
    └── stage3_normalize.txt  # ← 修正対象
```

**Structure Decision**: 既存の `stage3_normalize.txt` プロンプトファイルのみを修正。Python コードの変更は不要。

## Complexity Tracking

> 違反なし。シンプルなプロンプト拡張のみ。

## Phase 0: Research

### 調査項目

1. **Summary セクションのパターン**: Claude エクスポートファイルでの Summary 記述形式
2. **既存の英語処理**: 現在の `is_english_doc` フラグの動作確認

### 調査結果

**Decision**: プロンプトに Summary 翻訳ルールを追加
**Rationale**:
- Stage 3 は既にコンテンツ正規化を担当
- LLM 呼び出し回数を増やさない
- 既存の「断片的な英語メモ → 日本語」ルールを拡張

**Alternatives considered**:
- 新規 Stage 追加 → LLM 呼び出し増加、処理時間増のため却下
- Python コード修正で事前処理 → プロンプトで対応可能なため不要

## Phase 1: Design

### 変更内容

**ファイル**: `.claude/scripts/prompts/stage3_normalize.txt`

**追加ルール**:
```
4. **英語の Summary/Conversation Overview** → 日本語に翻訳
   - 例: "**Conversation Overview**\n\nThe user contacted Claude about..."
        → "**会話の概要**\n\nユーザーは〜についてClaudeに相談した..."
   - Summary セクションは常に日本語化（文書全体が英語でも例外なし）
```

### データモデル

変更なし（既存の `Stage3Result` を使用）

### API Contracts

変更なし（内部プロンプト修正のみ）

## Implementation Tasks

1. `stage3_normalize.txt` に Summary 翻訳ルールを追加
2. テストファイルで動作確認
3. 既存の英語サマリーファイルで検証

## Verification

- [x] 英語 Summary → 日本語に翻訳される
- [x] 日本語 Summary → 変更なし
- [x] 翻訳後も元の情報が保持される
- [ ] 処理時間が 20% 以上増加しない（後日検証）
