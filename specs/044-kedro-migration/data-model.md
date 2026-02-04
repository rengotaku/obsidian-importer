# Data Model: データパイプラインの構造的再設計（Kedro 移行）

**Date**: 2026-02-04
**Spec**: [spec.md](spec.md)

## Overview

Kedro 移行後のデータモデルは、現行の `ProcessingItem` dataclass を Kedro の PartitionedDataset に適合する辞書ベースの表現に変換する。ノード間のデータ受け渡しは `Dict[str, dict]`（partition_id → item_data）の形式で行い、DataCatalog が永続化を管理する。

## Entity Definitions

### E-1: RawConversation（Extract 入力）

プロバイダーからの生データ。形式はプロバイダー固有。

```python
# Claude: JSON object from conversations.json
{
    "uuid": str,                    # 会話 UUID
    "name": str | None,             # 会話名（None の場合あり）
    "created_at": str,              # ISO 8601
    "updated_at": str,              # ISO 8601
    "chat_messages": [              # メッセージ配列
        {
            "uuid": str,
            "sender": "human" | "assistant",
            "text": str,
            "created_at": str,
        }
    ],
}

# OpenAI: JSON object from conversations.json (ZIP 内)
{
    "id": str,
    "title": str | None,
    "create_time": float,           # Unix timestamp
    "mapping": {                    # ツリー構造
        "<node_id>": {
            "message": {
                "author": {"role": str},
                "content": {"parts": [str | dict]},
                "create_time": float,
            },
            "children": [str],
            "parent": str | None,
        }
    },
}

# GitHub Jekyll: Markdown file with YAML frontmatter
# (raw text string, parsed by ParseJekyllStep)
```

---

### E-2: ParsedItem（Extract 出力 / Transform 入力）

Extract ノードがプロバイダー固有形式をパースし、統一された中間表現に変換した結果。PartitionedDataset のパーティションとして保存。

```python
{
    "item_id": str,                 # UUID または SHA256 file_id
    "source_provider": str,         # "claude" | "openai" | "github"
    "source_path": str,             # 入力ファイルパス
    "conversation_name": str | None,# 会話名（プロバイダーから取得）
    "created_at": str | None,       # ISO 8601（プロバイダーから取得）
    "messages": [                   # 正規化されたメッセージ配列
        {
            "role": "human" | "assistant",
            "content": str,
        }
    ],
    "content": str,                 # フォーマット済み会話テキスト
    "file_id": str,                 # SHA256 ハッシュ（重複検出用）
    # チャンクメタデータ（チャンク分割時のみ）
    "is_chunked": bool,             # デフォルト: False
    "chunk_index": int | None,      # 0-based
    "total_chunks": int | None,
    "parent_item_id": str | None,
}
```

**Validation Rules**:
- `item_id` は必須・非空
- `content` は必須・10 文字以上（ValidateContentStep 相当）
- `messages` は 3 件以上（MIN_MESSAGES）
- チャンク: `is_chunked=True` の場合、`chunk_index`, `total_chunks`, `parent_item_id` は必須

---

### E-3: TransformedItem（Transform 出力 / Organize 入力 or Load 出力）

LLM による知識抽出・メタデータ生成・Markdown フォーマットを経た結果。

```python
{
    # ParsedItem のフィールドを継承
    "item_id": str,
    "source_provider": str,
    "source_path": str,
    "file_id": str,
    "created_at": str | None,
    "is_chunked": bool,
    "chunk_index": int | None,
    "total_chunks": int | None,
    "parent_item_id": str | None,

    # LLM 抽出結果（extract_knowledge ノード出力）
    "generated_metadata": {
        "title": str,               # LLM 生成タイトル（日本語）
        "summary": str,             # 要約（日本語に翻訳済み）
        "tags": list[str],          # LLM 生成タグ
    },

    # メタデータ（generate_metadata ノード出力）
    "metadata": {
        "title": str,               # generated_metadata.title のコピー
        "created": str,             # YYYY-MM-DD
        "tags": list[str],
        "source_provider": str,
        "file_id": str,
        "normalized": True,
    },

    # 最終コンテンツ（format_markdown ノード出力）
    "markdown_content": str,        # YAML frontmatter + 本文
    "output_filename": str,         # 出力ファイル名（サニタイズ済み）
}
```

---

### E-4: OrganizedItem（Organize 出力）

ジャンル判定・正規化を経て Vault 配置先が決定されたアイテム。

```python
{
    # TransformedItem のフィールドを継承
    "item_id": str,
    "file_id": str,
    "markdown_content": str,        # 正規化済み Markdown
    "output_filename": str,

    # Organize 追加フィールド
    "genre": str,                   # "engineer" | "business" | "economy" | "daily" | "other"
    "vault_path": str,              # "Vaults/エンジニア/" 等
    "final_path": str,              # vault_path + output_filename
}
```

---

## Entity Relationships

```
RawConversation (Provider-specific)
       │
       ▼ [Extract Node: parse + validate + chunk]
ParsedItem (Unified format)
       │
       ▼ [Transform Nodes: extract_knowledge → generate_metadata → format_markdown]
TransformedItem (LLM-enriched)
       │
       ▼ [Organize Nodes: classify_genre → normalize → clean → move_to_vault]
OrganizedItem (Vault-placed)
```

## DataCatalog Dataset Mapping

| Entity | Dataset Type | Catalog Name | Path |
|--------|-------------|--------------|------|
| RawConversation (Claude) | PartitionedDataset (json) | `raw_claude_conversations` | `data/01_raw/claude/` |
| RawConversation (OpenAI) | PartitionedDataset (json) | `raw_openai_conversations` | `data/01_raw/openai/` |
| RawConversation (GitHub) | PartitionedDataset (text) | `raw_github_posts` | `data/01_raw/github/` |
| ParsedItem | PartitionedDataset (json) | `parsed_items` | `data/02_intermediate/parsed/` |
| TransformedItem | PartitionedDataset (json) | `transformed_items` | `data/03_primary/transformed/` |
| Markdown Output | PartitionedDataset (text) | `markdown_notes` | `data/07_model_output/notes/` |
| OrganizedItem | PartitionedDataset (json) | `organized_items` | `data/07_model_output/organized/` |

## State Transitions

アイテムの処理状態は、どの PartitionedDataset にファイルが存在するかで暗黙的に表現される。明示的な status フィールドは不要（Kedro の冪等性パターン）。

```
[Not in any dataset] → raw_conversations に存在 → Extract 待ち
parsed_items に存在 → Transform 待ち（Extract 完了）
transformed_items に存在 → Organize 待ち（Transform 完了）
organized_items に存在 → 処理完了

失敗: 入力 dataset に存在するが出力 dataset に存在しない → 再実行時に再処理
```

## Provider-Specific Differences

| 差異 | Claude | OpenAI | GitHub |
|------|--------|--------|--------|
| 入力形式 | JSON（conversations.json） | ZIP（conversations.json 内） | git clone → Markdown |
| ID 生成 | uuid フィールド | id フィールド | SHA256(file_path) |
| メッセージ構造 | flat array | mapping tree（DFS 走査） | N/A（本文全体が content） |
| ロール変換 | sender: human/assistant | author.role: user→human, assistant→assistant | N/A |
| マルチモーダル | なし | 画像 `[Image: id]`, 音声 `[Audio: name]` | なし |
| チャンク分割 | 25000 文字超で分割 | 25000 文字超で分割 | なし |
| 日付抽出 | created_at フィールド | create_time (Unix) | frontmatter.date → ファイル名 → 正規表現 |
| タグ抽出 | LLM 生成 | LLM 生成 | frontmatter.tags/categories + LLM |
| スキップ条件 | messages < 3 | messages < 3 | draft: true, private: true |
| LLM 知識抽出 | あり | あり | なし（パススルー） |
