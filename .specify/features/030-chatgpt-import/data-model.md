# Data Model: ChatGPT エクスポートインポート

**Created**: 2026-01-22
**Status**: Complete

## Entity Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ChatGPT Export ZIP                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ conversations.  │  │   user.json     │  │ shared_conv... │  │
│  │     json        │  │                 │  │     .json      │  │
│  └────────┬────────┘  └─────────────────┘  └────────────────┘  │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│        ChatGPTConversation            │
│  ┌─────────────────────────────────┐  │
│  │ conversation_id: str            │  │
│  │ title: str                      │  │
│  │ create_time: float              │  │
│  │ update_time: float              │  │
│  │ mapping: dict[str, Node]        │  │
│  │ current_node: str               │  │
│  │ is_archived: bool               │  │
│  └─────────────────────────────────┘  │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│            Node (mapping)             │
│  ┌─────────────────────────────────┐  │
│  │ id: str                         │  │
│  │ parent: str | None              │  │
│  │ children: list[str]             │  │
│  │ message: ChatGPTMessage | None  │  │
│  └─────────────────────────────────┘  │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│          ChatGPTMessage               │
│  ┌─────────────────────────────────┐  │
│  │ id: str                         │  │
│  │ author: Author                  │  │
│  │ content: Content                │  │
│  │ create_time: float              │  │
│  │ status: str                     │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

## Entity Definitions

### ChatGPTConversation

会話全体を表すエンティティ。

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | `str` | 会話の一意識別子 |
| `id` | `str` | conversation_id と同じ値 |
| `title` | `str` | 会話のタイトル |
| `create_time` | `float` | 作成日時（Unix timestamp） |
| `update_time` | `float` | 更新日時（Unix timestamp） |
| `mapping` | `dict[str, Node]` | メッセージツリー |
| `current_node` | `str` | 現在の会話終端ノード |
| `is_archived` | `bool` | アーカイブ状態 |
| `gizmo_id` | `str | None` | カスタム GPT ID |
| `default_model_slug` | `str` | 使用モデル |

### Node

mapping 内のノード。ツリー構造を形成。

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | ノード ID |
| `parent` | `str | None` | 親ノード ID |
| `children` | `list[str]` | 子ノード ID リスト |
| `message` | `ChatGPTMessage | None` | メッセージ（ルートノードは None） |

### ChatGPTMessage

個別のメッセージ。

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | メッセージ ID |
| `author` | `Author` | 送信者情報 |
| `content` | `Content` | メッセージ内容 |
| `create_time` | `float` | 作成日時 |
| `update_time` | `float` | 更新日時 |
| `status` | `str` | ステータス（"finished_successfully" 等） |
| `metadata` | `dict` | 追加メタデータ |

### Author

メッセージの送信者。

| Field | Type | Description |
|-------|------|-------------|
| `role` | `str` | "user", "assistant", "system", "tool" |
| `name` | `str | None` | カスタム名 |
| `metadata` | `dict` | 追加情報 |

### Content

メッセージの内容。マルチモーダル対応。

| Field | Type | Description |
|-------|------|-------------|
| `content_type` | `str` | "text", "multimodal_text" |
| `parts` | `list[str | dict]` | コンテンツパーツ |

**parts の要素**:
- `str`: テキストコンテンツ
- `dict`: マルチモーダルコンテンツ（画像など）

マルチモーダル dict:
```json
{
  "content_type": "image_asset_pointer",
  "asset_pointer": "sediment://file_xxxxx",
  "size_bytes": 292065,
  "width": 3060,
  "height": 4080
}
```

## 変換マッピング

### ChatGPT → ProcessingItem

| ChatGPT Field | ProcessingItem Field | 変換 |
|---------------|---------------------|------|
| `conversation_id` | `metadata.conversation_uuid` | そのまま |
| `title` | `metadata.conversation_name` | そのまま |
| `create_time` | `metadata.created_at` | Unix → ISO 8601 |
| (hash) | `item_id` | コンテンツから SHA256 生成 |
| (serialized) | `content` | JSON 文字列化 |

### ChatGPTMessage → chat_messages

| ChatGPT Field | 変換後 | 処理 |
|---------------|--------|------|
| `author.role: "user"` | `sender: "human"` | ロール変換 |
| `author.role: "assistant"` | `sender: "assistant"` | そのまま |
| `author.role: "system"` | - | 除外 |
| `author.role: "tool"` | - | 除外 |
| `content.parts` | `text` | 結合してテキスト化 |

### ProcessingItem → Markdown

| Field | Markdown Location |
|-------|-------------------|
| `metadata.conversation_name` | frontmatter: `title` |
| `metadata.created_at` | frontmatter: `created` |
| (LLM generated) | frontmatter: `summary` |
| (LLM generated) | frontmatter: `tags` |
| `"openai"` | frontmatter: `source_provider` |
| `item_id` | frontmatter: `item_id` |
| `content` | body: `# まとめ`, `# 主要な学び` |

## Validation Rules

### ChatGPTConversation

- `conversation_id` は必須かつ一意
- `mapping` に少なくとも 1 つのノードが必要
- `current_node` は `mapping` 内に存在する必要がある

### ChatGPTMessage

- `author.role` は "user", "assistant", "system", "tool" のいずれか
- `content.parts` は空でない配列
- user/assistant メッセージの `parts` には少なくとも 1 つの文字列要素が必要

### メッセージ数カウント

- system, tool メッセージはカウントに含めない
- MIN_MESSAGES（デフォルト 3）未満の会話はスキップ

## State Transitions

```
┌──────────┐     discover     ┌──────────┐
│   ZIP    │ ───────────────► │ PENDING  │
└──────────┘                  └────┬─────┘
                                   │
                              extract_stage
                                   │
                                   ▼
                             ┌──────────┐
                             │PROCESSING│
                             └────┬─────┘
                                  │
                         ┌────────┼────────┐
                         │        │        │
                         ▼        ▼        ▼
                    ┌────────┐ ┌────────┐ ┌────────┐
                    │COMPLETED│ │SKIPPED │ │ FAILED │
                    └────────┘ └────────┘ └────────┘
```

**SKIPPED 条件**:
- メッセージ数 < MIN_MESSAGES
- file_id が @index に既存（重複）かつ更新なし

**FAILED 条件**:
- JSON パースエラー
- mapping ツリー走査エラー
- LLM 抽出エラー（リトライ後も失敗）
