# Implementation Plan: LLM レスポンス形式をマークダウンに変更

**Branch**: `042-llm-markdown-response` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/042-llm-markdown-response/spec.md`

## Summary

LLM（Ollama）への知識抽出リクエストのレスポンス形式を JSON からマークダウンに変更する。JSON 形式の強制が LLM の出力品質を低下させる懸念に対処するため、LLM にはマークダウン構造で自由に応答させ、返されたマークダウンを正規表現ベースのパーサーで構造化データ（dict）に変換する。既存パイプラインとの後方互換性を維持するため、パーサーの出力形式は現行の `parse_json_response()` と同一とする。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（リトライ）、ollama（LLM API）、標準ライブラリ（re, json, dataclasses）
**Storage**: ファイルシステム（JSONL, JSON, Markdown）- セッションフォルダ構造
**Testing**: unittest（標準ライブラリ）、`make test` で実行
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project（既存 ETL パイプライン）
**Performance Goals**: LLM レスポンスのパース処理は < 10ms（正規表現ベース）
**Constraints**: 外部ライブラリ追加なし。標準ライブラリのみでパーサーを実装
**Scale/Scope**: 2 プロンプトテンプレート変更、1 パーサーモジュール新規作成、既存テスト更新

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Obsidian Markdown Compliance | ✅ PASS | 出力ファイルのフォーマットは変更なし。frontmatter 必須フィールド維持 |
| Normalization First | ✅ PASS | normalized フィールドの処理は変更なし |
| Genre-Based Organization | ✅ PASS | 振り分けロジックへの影響なし |
| Automation with Oversight | ✅ PASS | LLM 出力品質の変更は目視確認で検証（SC-003） |
| Vault Independence | ✅ PASS | Vault 構造への影響なし |

**Pre-design check**: PASS（全ゲート通過）

## Project Structure

### Documentation (this feature)

```text
specs/042-llm-markdown-response/
├── plan.md              # This file
├── research.md          # Phase 0 output - 技術調査結果
├── data-model.md        # Phase 1 output - データモデル定義
├── quickstart.md        # Phase 1 output - 変更の概要
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/etl/
├── utils/
│   ├── ollama.py                  # 変更: parse_markdown_response() 追加
│   └── knowledge_extractor.py     # 変更: JSON パース → マークダウンパース呼び出し
├── prompts/
│   ├── knowledge_extraction.txt   # 変更: JSON → マークダウン出力指示
│   └── summary_translation.txt    # 変更: JSON → マークダウン出力指示
└── tests/
    ├── test_ollama.py             # 変更: マークダウンパースのテスト追加
    └── test_knowledge_extractor.py # 変更: マークダウンレスポンスのテスト更新
```

**Structure Decision**: 既存の `src/etl/` プロジェクト構造をそのまま使用。新規ファイルの追加は不要。`utils/ollama.py` にパーサー関数を追加し、プロンプトテンプレートを更新する。

## Post-Design Constitution Re-Check

| Gate | Status | Notes |
|------|--------|-------|
| Obsidian Markdown Compliance | ✅ PASS | `KnowledgeDocument.to_markdown()` の出力形式は不変 |
| Normalization First | ✅ PASS | frontmatter 生成ロジック不変 |
| Quality Standards | ✅ PASS | マークダウンパーサーの品質はユニットテストで保証 |

**Post-design check**: PASS（全ゲート通過）

## Complexity Tracking

> 憲法違反なし。追加の正当化不要。
