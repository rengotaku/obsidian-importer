# Implementation Plan: 大規模ファイルのチャンク分割処理

**Branch**: `020-large-file-chunking` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-large-file-chunking/spec.md`

## Summary

25,000文字以上の会話ファイルをメッセージ境界で自動分割し、各チャンクを個別にLLM処理して連番付きファイル（例: `タイトル_001.md`）として出力する。既存の `KnowledgeExtractor.extract()` メソッドを拡張し、チャンク分割ロジックを追加する。

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリのみ）
**Primary Dependencies**: なし（urllib, json, pathlib - 既存依存のみ）
**Storage**: ファイルシステム（Markdown）
**Testing**: unittest（`make test`）
**Target Platform**: Linux
**Project Type**: single
**Performance Goals**: チャンク分割による処理時間増加 2倍以内（SC-002）
**Constraints**: メモリ効率的な処理（大規模ファイルでもメモリ爆発しない）
**Scale/Scope**: 50,000〜132,000文字の会話ファイル処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力は既存形式を維持 |
| III. Normalization First | ✅ Pass | 正規化処理は既存を利用 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ Pass | ログ出力で進捗可視化 |

**Gate Result**: ✅ PASS - 全原則に準拠

## Project Structure

### Documentation (this feature)

```text
specs/020-large-file-chunking/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
development/scripts/llm_import/
├── common/
│   ├── knowledge_extractor.py  # 修正: チャンク処理ロジック追加
│   ├── chunker.py              # 新規: チャンク分割モジュール
│   └── ollama.py               # 既存: num_ctx=65536 に更新済み
├── tests/
│   ├── test_chunker.py         # 新規: チャンクテスト
│   └── test_knowledge_extractor.py  # 修正: チャンク統合テスト追加
└── cli.py                      # 既存: 変更不要（上位レイヤー）
```

**Structure Decision**: 既存の `common/` ディレクトリ内に `chunker.py` を新規追加。`KnowledgeExtractor` クラスを拡張してチャンク処理を統合。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |

**注記**: 本機能は既存アーキテクチャに沿った拡張であり、憲法違反なし。
