# Data Model: RAG Migration

**Feature**: 001-rag-migration-plan
**Date**: 2026-01-18

## Entity Relationship

```
┌─────────────────┐       ┌─────────────────┐
│    Vault        │       │    Document     │
├─────────────────┤       ├─────────────────┤
│ name            │1     *│ file_path       │
│ path            │───────│ title           │
│                 │       │ content         │
└─────────────────┘       │ metadata        │
                          │ vault_name      │
                          └────────┬────────┘
                                   │1
                                   │
                                   │*
                          ┌────────┴────────┐
                          │     Chunk       │
                          ├─────────────────┤
                          │ id              │
                          │ content         │
                          │ embedding       │
                          │ doc_id          │
                          │ position        │
                          └────────┬────────┘
                                   │*
                                   │
                                   │1
                          ┌────────┴────────┐
                          │  SearchResult   │
                          ├─────────────────┤
                          │ chunk           │
                          │ score           │
                          │ highlights      │
                          └─────────────────┘
```

---

## Entities

### Vault

ナレッジベースのトップレベル分類単位。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Vault 名 | enum: エンジニア, ビジネス, 経済, 日常, その他 |
| `path` | Path | Vault ディレクトリパス | 存在するディレクトリ |

**Validation Rules**:
- name は定義済みジャンルのいずれかに一致
- path は `Vaults/` 配下に存在

---

### Document

インデックス対象の Markdown ファイル。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `file_path` | Path | ファイルの絶対パス | 存在する .md ファイル |
| `title` | string | frontmatter の title | 必須、200文字以内 |
| `content` | string | Markdown 本文 | frontmatter 除く |
| `metadata` | DocumentMeta | 付随メタデータ | 下記参照 |
| `vault_name` | string | 所属 Vault | Vault.name の外部キー |

**DocumentMeta**:
| Field | Type | Description |
|-------|------|-------------|
| `tags` | list[string] | タグリスト |
| `created` | date | 作成日 (YYYY-MM-DD) |
| `normalized` | bool | 正規化フラグ |
| `file_id` | string | ファイル追跡用ハッシュ |

**Validation Rules**:
- `normalized == True` のファイルのみインデックス対象
- `title` はファイルシステム禁止文字を含まない

---

### Chunk

ドキュメントを分割したテキスト単位。Qdrant に格納。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | 一意識別子 | UUID v4 |
| `content` | string | チャンクテキスト | 512 tokens 以下 |
| `embedding` | list[float] | ベクトル表現 | 1024 次元 (bge-m3) |
| `doc_id` | string | 元ドキュメント参照 | Document.file_path のハッシュ |
| `position` | int | ドキュメント内の位置 | 0-indexed |
| `metadata` | ChunkMeta | 検索用メタデータ | 下記参照 |

**ChunkMeta** (Qdrant payload):
| Field | Type | Description |
|-------|------|-------------|
| `file_path` | string | 元ファイルパス |
| `title` | string | ドキュメントタイトル |
| `vault` | string | Vault 名 |
| `tags` | list[string] | タグリスト |
| `created` | string | 作成日 |

**Validation Rules**:
- embedding は 1024 次元の float 配列
- position は 0 以上の整数

---

### Query

ユーザーからの検索リクエスト。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `text` | string | 検索クエリ | 1-1000 文字 |
| `filters` | QueryFilters | フィルタ条件 | オプション |
| `top_k` | int | 取得件数 | 1-100、デフォルト 5 |
| `mode` | QueryMode | 検索モード | search / qa |

**QueryFilters**:
| Field | Type | Description |
|-------|------|-------------|
| `vaults` | list[string] | Vault 絞り込み |
| `tags` | list[string] | タグ絞り込み (AND) |
| `date_from` | date | 作成日下限 |
| `date_to` | date | 作成日上限 |

**QueryMode** (enum):
- `search`: ドキュメント検索のみ
- `qa`: 質問応答（LLM 回答生成）

---

### SearchResult

検索結果の単一項目。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `chunk` | Chunk | マッチしたチャンク | 必須 |
| `score` | float | 類似度スコア | 0.0-1.0 |
| `highlights` | list[string] | ハイライト箇所 | オプション |

---

### Answer

Q&A モードの回答。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `text` | string | 生成された回答 | 必須 |
| `sources` | list[SearchResult] | 参照元 | 1件以上 |
| `confidence` | float | 回答の確信度 | 0.0-1.0 |

---

## State Transitions

### Document Indexing State

```
┌──────────────┐     scan      ┌──────────────┐
│  Unindexed   │──────────────►│   Scanned    │
└──────────────┘               └──────┬───────┘
                                      │ chunk
                                      ▼
                               ┌──────────────┐
                               │   Chunked    │
                               └──────┬───────┘
                                      │ embed
                                      ▼
┌──────────────┐    delete     ┌──────────────┐
│   Deleted    │◄──────────────│   Indexed    │
└──────────────┘               └──────────────┘
                                      ▲
                                      │ update
                                      │
                               ┌──────────────┐
                               │   Modified   │
                               └──────────────┘
```

### Query Processing State

```
┌──────────────┐    embed      ┌──────────────┐
│   Received   │──────────────►│   Embedded   │
└──────────────┘               └──────┬───────┘
                                      │ retrieve
                                      ▼
                               ┌──────────────┐
                               │  Retrieved   │
                               └──────┬───────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │ mode=search                       │ mode=qa
                    ▼                                   ▼
             ┌──────────────┐                   ┌──────────────┐
             │  Completed   │                   │  Generating  │
             │  (results)   │                   └──────┬───────┘
             └──────────────┘                          │ generate
                                                       ▼
                                                ┌──────────────┐
                                                │  Completed   │
                                                │  (answer)    │
                                                └──────────────┘
```

---

## Qdrant Collection Schema

```json
{
  "collection_name": "obsidian_knowledge",
  "vectors": {
    "size": 1024,
    "distance": "Cosine"
  },
  "payload_schema": {
    "file_path": { "type": "keyword" },
    "title": { "type": "text" },
    "vault": { "type": "keyword" },
    "tags": { "type": "keyword[]" },
    "created": { "type": "datetime" },
    "position": { "type": "integer" },
    "content": { "type": "text" }
  }
}
```
