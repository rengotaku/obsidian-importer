# Data Model: ETL Import パリティ実装

**Generated**: 2026-01-19
**Status**: Complete

## Entity Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Pipeline Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  conversations.json                                              │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────────┐                                            │
│  │ ProcessingItem  │ ◄── Extract Stage で作成                   │
│  │  (item_id)      │                                            │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │ KnowledgeDoc    │ ──► │ ExtractionResult│                    │
│  │  (file_id)      │     │  (success/error)│                    │
│  └────────┬────────┘     └─────────────────┘                    │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │ Markdown File   │ ──► │ StageLogRecord  │                    │
│  │ (.md output)    │     │ (JSONL logging) │                    │
│  └─────────────────┘     └─────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Entities

### ProcessingItem (既存 - src/etl/core/models.py)

パイプラインを流れるアイテム。各 Stage/Step で更新される。

| Field | Type | Description |
|-------|------|-------------|
| item_id | str | 一意識別子（conversation UUID） |
| source_path | Path | 元ファイルパス |
| current_step | str | 現在の処理ステップ名 |
| status | ItemStatus | PENDING → PROCESSING → SUCCESS/FAILED/SKIPPED |
| metadata | dict[str, Any] | 任意メタデータ（knowledge_extracted, file_id 等） |
| content | str \| None | 抽出後の生コンテンツ |
| transformed_content | str \| None | 変換後コンテンツ（Markdown） |
| output_path | Path \| None | 出力先パス |
| error | str \| None | エラーメッセージ |

**State Transitions**:
```
PENDING → PROCESSING → SUCCESS
                    → FAILED (error set)
                    → SKIPPED (skip_reason in metadata)
```

---

### KnowledgeDocument (src/etl/utils/knowledge_extractor.py)

Ollama で抽出されたナレッジ。to_markdown() で Markdown 出力。

| Field | Type | Description |
|-------|------|-------------|
| title | str | タイトル（frontmatter） |
| summary | str | 1行要約（frontmatter） |
| created | str | 作成日 YYYY-MM-DD |
| source_provider | str | "claude" |
| source_conversation | str | 元会話 UUID |
| summary_content | str | 構造化まとめ（本文） |
| key_learnings | list[str] | 主要な学び |
| code_snippets | list[CodeSnippet] | コードスニペット |
| file_id | str | 12文字16進数ハッシュ |
| normalized | bool | True |

**Validation Rules**:
- title: 非空
- summary: 非空、100文字以内推奨
- created: YYYY-MM-DD 形式
- file_id: 12文字16進数（SHA256 先頭48bit）

---

### ExtractionResult (src/etl/utils/knowledge_extractor.py)

Ollama 抽出処理の結果。

| Field | Type | Description |
|-------|------|-------------|
| success | bool | 成功フラグ |
| document | KnowledgeDocument \| None | 成功時のドキュメント |
| error | str \| None | 失敗時のエラーメッセージ |
| raw_response | str \| None | LLM 生レスポンス |
| user_prompt | str \| None | LLM に送信したプロンプト |

---

### ErrorDetail (src/etl/utils/error_writer.py)

エラー詳細ファイル出力用。

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | セッション ID |
| conversation_id | str | 会話 UUID |
| conversation_title | str | 会話タイトル |
| timestamp | datetime | エラー発生時刻 |
| error_type | str | json_parse, no_json, timeout 等 |
| error_message | str | エラーメッセージ |
| original_content | str | 元の会話内容 |
| llm_prompt | str | LLM プロンプト |
| stage | str | phase1, phase2 |
| error_position | int \| None | エラー位置 |
| error_context | str \| None | エラー周辺テキスト |
| llm_output | str \| None | LLM 生出力 |

---

### StageLogRecord (新規 - フレームワーク自動出力)

pipeline_stages.jsonl の1レコード。

| Field | Type | Description |
|-------|------|-------------|
| timestamp | str | ISO8601 形式 |
| session_id | str | セッション ID |
| filename | str | 処理ファイル名 |
| stage | str | extract, transform, load |
| step | str | ステップ名 |
| timing_ms | int | 処理時間（ミリ秒） |
| status | str | success, failed, skipped |
| file_id | str \| None | 成功時の file_id |
| skipped_reason | str \| None | スキップ時の理由 |
| before_chars | int \| None | 変換前文字数 |
| after_chars | int \| None | 変換後文字数 |
| diff_ratio | float \| None | after_chars / before_chars |

---

### Chunk (src/etl/utils/chunker.py)

分割されたチャンク。

| Field | Type | Description |
|-------|------|-------------|
| index | int | チャンク番号（0-indexed） |
| messages | list | チャンク内メッセージ |
| char_count | int | 文字数 |
| has_overlap | bool | オーバーラップ含むか |
| overlap_count | int | オーバーラップメッセージ数 |

---

### ChunkedConversation (src/etl/utils/chunker.py)

チャンク分割された会話。

| Field | Type | Description |
|-------|------|-------------|
| original | BaseConversation | 元の会話 |
| chunks | list[Chunk] | チャンクリスト |
| total_chars | int | 元の総文字数 |
| chunk_size | int | 使用した閾値 |

---

## Relationships

```
ProcessingItem (1) ─────contains────► (1) KnowledgeDocument
                                              │
                                              │ serializes to
                                              ▼
                                         Markdown File
                                              │
                                              │ file_id reference
                                              ▼
                                         @index File

ProcessingItem (1) ─────on error────► (1) ErrorDetail
                                              │
                                              │ writes to
                                              ▼
                                         errors/*.md

Conversation (1) ─────if large────► (N) Chunk
                                         │
                                         │ each produces
                                         ▼
                                    KnowledgeDocument

Stage.run() ─────auto logs────► StageLogRecord
                                      │
                                      │ appends to
                                      ▼
                                 pipeline_stages.jsonl
```

---

## Integration Points

### ProcessingItem.metadata Keys

| Key | Type | Set by | Description |
|-----|------|--------|-------------|
| knowledge_extracted | bool | ExtractKnowledgeStep | 知識抽出完了フラグ |
| file_id | str | GenerateMetadataStep | 生成された file_id |
| is_chunked | bool | ExtractKnowledgeStep | チャンク分割されたか |
| chunk_index | int | ExtractKnowledgeStep | チャンク番号 |
| skip_reason | str | ValidateStructureStep | スキップ理由 |
| summary_translated | bool | ExtractKnowledgeStep | Summary 翻訳フラグ |

### KnowledgeDocument.to_markdown() 出力形式

```yaml
---
title: {title}
summary: {summary}
created: {created}
source_provider: {source_provider}
source_conversation: {source_conversation}
file_id: {file_id}
normalized: true
---

# まとめ

{summary_content}

# 主要な学び

- {learning_1}
- {learning_2}

# コードスニペット

## {snippet.description}

```{snippet.language}
{snippet.code}
```
```
