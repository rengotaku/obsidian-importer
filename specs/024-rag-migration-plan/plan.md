# Implementation Plan: RAG Migration

**Branch**: `001-rag-migration-plan` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-migration-plan/spec.md`

## Summary

Obsidian ナレッジベースに RAG（Retrieval-Augmented Generation）システムを導入し、セマンティック検索と質問応答機能を実現する。Haystack 2.x フレームワークを採用し、リモート Embedding サーバー（bge-m3 @ ollama-server.local）とローカル LLM（gpt-oss:20b）を組み合わせた分散構成で実装する。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: haystack-ai, ollama-haystack, qdrant-haystack, structlog
**Storage**: Qdrant (ローカルファイル永続化 @ `data/qdrant/`)
**Testing**: unittest (標準ライブラリ、既存パイプラインと統一)
**Target Platform**: Linux (Ubuntu/Debian)
**Project Type**: single (CLI ツール)
**Performance Goals**: 検索 3秒以内、インデックス作成 10分以内 (1000ドキュメント)
**Constraints**: 8GB メモリ環境で動作、ローカル完結（クラウド依存なし）
**Scale/Scope**: 1000 ドキュメント規模、5 Vault 対象

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Vault Independence** | ✅ PASS | 各 Vault を独立してインデックス化、フィルタリング可能 |
| **II. Obsidian Markdown Compliance** | ✅ PASS | frontmatter メタデータを活用してインデックス作成 |
| **III. Normalization First** | ✅ PASS | `normalized: true` のファイルのみをインデックス対象とする |
| **IV. Genre-Based Organization** | ✅ PASS | Vault/ジャンルでフィルタリング検索可能 |
| **V. Automation with Oversight** | ✅ PASS | インデックス更新は手動トリガー、自動処理なし |

**Gate Result**: ✅ PASS - 全原則に適合

## Edge Case Decisions

| Edge Case | Decision | Rationale |
|-----------|----------|-----------|
| 大量ドキュメント（1000件+）のインデックス時間 | SC-004 で検証（10分以内） | バッチ処理前提、進捗表示で体感改善 |
| 日英混在ドキュメントの検索精度 | bge-m3 の trilingual 対応で吸収 | 追加対応不要、SC-002 で検証 |
| 画像を含むドキュメント | テキスト部分のみインデックス | 画像埋め込みは Out of Scope |
| インデックス作成中の検索 | 既存インデックスで検索継続 | Qdrant の collection 分離で対応 |

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-migration-plan/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── rag/
    ├── __init__.py
    ├── config.py           # 設定・定数
    ├── cli.py              # CLI エントリポイント
    ├── clients/
    │   ├── __init__.py
    │   └── ollama.py       # リモート Ollama クライアント
    ├── stores/
    │   ├── __init__.py
    │   └── qdrant.py       # Qdrant セットアップ
    └── pipelines/
        ├── __init__.py
        ├── indexing.py     # インデックス作成パイプライン
        └── query.py        # 検索・Q&A パイプライン

tests/
└── rag/
    ├── __init__.py
    ├── test_config.py
    ├── test_ollama_client.py
    ├── test_indexing.py
    └── test_query.py

data/
└── qdrant/                 # Qdrant 永続化ディレクトリ
```

**Structure Decision**: Single project 構成を採用。既存の `development/scripts/` と共存し、新規 RAG 機能は `/src/rag/` に配置。

## Complexity Tracking

> 該当なし - Constitution Check に違反なし
