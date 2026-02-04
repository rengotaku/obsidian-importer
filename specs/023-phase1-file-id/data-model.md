# Data Model: 全工程での file_id 付与・維持

**Feature**: 023-phase1-file-id
**Date**: 2026-01-18

## Entities

### 1. file_id

ファイルを一意に識別する12文字の16進数ハッシュ。

| Attribute | Type | Description |
|-----------|------|-------------|
| value | string | 12文字の16進数（SHA-256先頭48ビット） |

**生成ルール**:
```
input = "{content}\n---\n{filepath.as_posix()}"
file_id = sha256(input.encode("utf-8")).hexdigest()[:12]
```

**例**: `ab7d3d1c62f4`

---

### 2. Parsed File (Phase 1 出力)

Phase 1 で生成される中間 Markdown ファイル。

**Frontmatter**:
```yaml
---
title: {conversation.title}
uuid: {conversation.uuid}
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags:
  - claude-export
file_id: {12文字16進数}  # NEW
---
```

**ファイルパス**: `.staging/@plan/import/{session_id}/parsed/conversations/{title}.md`

---

### 3. @index File (Phase 2 出力)

Phase 2 で生成されるナレッジファイル。

**Frontmatter**:
```yaml
---
title: {extracted_title}
summary: {summary}
created: {YYYY-MM-DD}
source_provider: claude
source_conversation: {uuid}
file_id: {12文字16進数}  # Phase 1 から継承
normalized: false
---
```

**ファイルパス**: `.staging/@index/{title}.md`

---

### 4. Vaults File (organize 出力)

organize 後の最終ファイル。

**Frontmatter**:
```yaml
---
title: {title}
tags:
  - {tag1}
  - {tag2}
created: {YYYY-MM-DD}
summary: {summary}
related:
  - "[[Related Note 1]]"
file_id: {12文字16進数}  # @index から継承または新規生成
normalized: true
---
```

**ファイルパス**: `Vaults/{genre}/{title}.md`

---

### 5. pipeline_stages.jsonl Entry

パイプラインステージの実行ログエントリ。

**JSON Schema**:
```json
{
  "timestamp": "2026-01-18T09:53:22",
  "filename": "会話タイトル",
  "stage": "phase1" | "phase2",
  "executed": true | false,
  "timing_ms": 1234,
  "skipped_reason": null | "reason",
  "file_id": "ab7d3d1c62f4",  // NEW
  "before_chars": 1576,       // Phase 2 only
  "after_chars": 552,         // Phase 2 only
  "diff_ratio": -0.65         // Phase 2 only
}
```

**ファイルパス**: `.staging/@plan/import/{session_id}/pipeline_stages.jsonl`

---

### 6. ProcessedEntry (state.json)

処理済み会話のエントリ（既存、022-import-file-id で file_id 追加済み）。

**JSON Schema**:
```json
{
  "id": "uuid",
  "provider": "claude",
  "input_file": "path/to/parsed.md",
  "output_file": "path/to/output.md",
  "processed_at": "2026-01-18T09:53:50",
  "status": "success" | "error" | "skipped",
  "skip_reason": null | "reason",
  "error_message": null | "message",
  "file_id": "ab7d3d1c62f4"
}
```

---

## State Transitions

### file_id のライフサイクル

```
[生成] Phase 1 (parsed)
    ↓
[継承] Phase 2 (@index/)
    ↓
[維持] Organize (Vaults/)
```

### 「なければ生成、あれば維持」ロジック

```python
def get_or_generate_file_id(content: str, filepath: Path, existing_file_id: str | None) -> str:
    if existing_file_id is not None:
        return existing_file_id  # 維持
    return generate_file_id(content, filepath)  # 生成
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| file_id | `/^[0-9a-f]{12}$/` (12文字16進数) |
| file_id | 同一ファイルなら同一値（決定論的） |
| file_id | null 許容（後方互換性） |

---

## Relationships

```
ClaudeConversation (1) ──creates──> (1) ParsedFile
ParsedFile (1) ──transforms──> (1) @indexFile
@indexFile (1) ──organizes──> (1) VaultsFile

All files share the same file_id throughout lifecycle
```
