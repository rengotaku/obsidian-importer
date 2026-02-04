# Data Model: ChatGPTExtractor Steps分離リファクタリング

**Date**: 2026-01-24
**Status**: Draft

## Entity Changes

### 1. BaseStep (Modified)

現在の `process()` 戻り値型を拡張し、1:N 展開をサポート。

```text
BaseStep
├── name: str (property, abstract)
├── process(item: ProcessingItem) -> ProcessingItem | list[ProcessingItem]  # MODIFIED
├── validate_input(item: ProcessingItem) -> bool
└── on_error(item: ProcessingItem, error: Exception) -> ProcessingItem | None
```

**BEFORE**:
```python
@abstractmethod
def process(self, item: ProcessingItem) -> ProcessingItem:
    ...
```

**AFTER**:
```python
@abstractmethod
def process(self, item: ProcessingItem) -> ProcessingItem | list[ProcessingItem]:
    ...
```

**Validation Rules**:
- 戻り値が list の場合、空リストは禁止（少なくとも 1 アイテム必須）
- list 内の各アイテムは有効な ProcessingItem であること
- 単一アイテム返却の場合は既存動作と互換

---

### 2. ProcessingItem (Unchanged - metadata 規約追加のみ)

既存フィールドは変更なし。metadata 内の規約を追加。

```text
ProcessingItem
├── item_id: str
├── source_path: Path
├── current_step: str
├── status: ItemStatus
├── metadata: dict[str, Any]  # 1:N 展開用フィールド追加（規約）
├── content: str | None
├── transformed_content: str | None
├── output_path: Path | None
└── error: str | None
```

**Metadata Schema for 1:N Expanded Items** (規約追加):
```yaml
metadata:
  # 展開元追跡（既存 chunking と統一）
  parent_item_id: str      # 展開元アイテムの item_id
  expansion_index: int     # 0-based 展開インデックス
  total_expanded: int      # 展開後の総アイテム数

  # ChatGPT 固有
  conversation_uuid: str
  conversation_name: str
  created_at: str
  source_provider: "openai"
  source_type: "conversation"
```

---

### 3. New Step Classes (ChatGPT Extract)

#### 3.1 ReadZipStep (1:1)

```text
ReadZipStep (extends BaseStep)
├── name: "read_zip"
├── process(item) -> ProcessingItem
│   BEFORE: item.content = None
│   AFTER:  item.content = raw JSON string from conversations.json
│           item.metadata.zip_path = <zip file path>
│           item.metadata.extracted_file = "conversations.json"
└── validate_input(item) -> bool
    Returns False if item.source_path is not a ZIP file
```

**State Transitions**:
- input: `content=None, status=PENDING`
- output: `content=<json_string>, status=PENDING`
- error: `status=FAILED, error=<message>`

#### 3.2 ParseConversationsStep (1:N)

```text
ParseConversationsStep (extends BaseStep)
├── name: "parse_conversations"
├── process(item) -> list[ProcessingItem]  # 1:N 展開
│   BEFORE: item.content = '{"conversations": [...]}'
│   AFTER:  [
│             ProcessingItem(item_id=<conv_uuid_1>, content=<conv_dict_1>, ...),
│             ProcessingItem(item_id=<conv_uuid_2>, content=<conv_dict_2>, ...),
│             ...
│           ]
└── validate_input(item) -> bool
    Returns False if item.content is None or not valid JSON
```

**Output Item Metadata**:
```yaml
metadata:
  parent_item_id: <original zip item_id>
  expansion_index: 0..N-1
  total_expanded: N
  conversation_uuid: <uuid>
  conversation_name: <name>
  created_at: <timestamp>
  source_provider: "openai"
  source_type: "conversation"
```

**State Transitions**:
- input: 1 item with `content=<full_json>`
- output: N items with `content=<individual_conversation_dict>`
- error: 1 item with `status=FAILED`

#### 3.3 ConvertFormatStep (1:1)

```text
ConvertFormatStep (extends BaseStep)
├── name: "convert_format"
├── process(item) -> ProcessingItem
│   BEFORE: item.content = {"uuid": "xxx", "mapping": {...}}  # ChatGPT format
│   AFTER:  item.content = [{"sender": "human", ...}, ...]    # Claude format
│           item.metadata.message_count = <count>
│           item.metadata.format = "claude"
└── validate_input(item) -> bool
    Returns False if item.content is not a dict with 'mapping' key
```

**State Transitions**:
- input: `content=<chatgpt_dict>`
- output: `content=<claude_messages_json>`

#### 3.4 ValidateMinMessagesStep (1:1)

```text
ValidateMinMessagesStep (extends BaseStep)
├── name: "validate_min_messages"
├── process(item) -> ProcessingItem
│   BEFORE: item.content = [messages...]
│   AFTER:  item.status = SKIPPED (if < MIN_MESSAGES)
│           item.metadata.skip_reason = "skipped_short"
│           item.metadata.message_count = <count>
│           OR unchanged (if >= MIN_MESSAGES)
└── validate_input(item) -> bool
    Returns False if item.content is not a list
```

**State Transitions**:
- input: `content=<messages>, status=PENDING`
- output (pass): `status=PENDING` (unchanged)
- output (skip): `status=SKIPPED, metadata.skip_reason="skipped_short"`

---

### 4. ChatGPTExtractor (Modified)

```text
ChatGPTExtractor (extends BaseStage)
├── stage_type: StageType.EXTRACT
├── steps: [ReadZipStep, ParseConversationsStep, ConvertFormatStep, ValidateMinMessagesStep]
└── discover_items(input_path) -> Iterator[ProcessingItem]
    BEFORE: ZIP 読み込み、パース、変換、スキップ判定を全て実行
    AFTER:  ZIP ファイル発見のみ、content=None で ProcessingItem を yield
```

**discover_items() BEFORE**:
```python
def discover_items(self, input_path):
    # 1. Find ZIP
    # 2. Read ZIP and extract conversations.json
    # 3. Parse JSON
    # 4. For each conversation: convert format, check MIN_MESSAGES
    # 5. Yield ProcessingItem with content already set
```

**discover_items() AFTER**:
```python
def discover_items(self, input_path):
    # 1. Find ZIP file(s)
    # 2. Yield ProcessingItem(content=None) for each ZIP
    #    - Actual processing delegated to Steps
```

---

### 5. Session (Modified)

session.json の `phases` フィールドを拡張し、フェーズ完了時の統計を記録。

```text
Session
├── session_id: str
├── base_path: Path
├── created_at: datetime
├── status: SessionStatus
├── phases: dict[str, PhaseStats]  # MODIFIED: list[str] → dict[str, PhaseStats]
└── debug_mode: bool

PhaseStats (New)
├── status: str           # "completed", "partial", "failed", "crashed"
├── success_count: int    # 成功した item 数
├── error_count: int      # 失敗した item 数
├── completed_at: str     # ISO 形式タイムスタンプ
└── error: str | None     # 例外発生時のエラーメッセージ（オプション）
```

**session.json BEFORE**:
```json
{
  "session_id": "20260124_120000",
  "created_at": "2026-01-24T12:00:00",
  "status": "completed",
  "phases": ["import"],
  "debug_mode": true
}
```

**session.json AFTER**:
```json
{
  "session_id": "20260124_120000",
  "created_at": "2026-01-24T12:00:00",
  "status": "completed",
  "phases": {
    "import": {
      "status": "completed",
      "success_count": 42,
      "error_count": 3,
      "completed_at": "2026-01-24T12:05:30"
    }
  },
  "debug_mode": true
}
```

**session.json AFTER (例外発生時)**:
```json
{
  "session_id": "20260124_120000",
  "created_at": "2026-01-24T12:00:00",
  "status": "failed",
  "phases": {
    "import": {
      "status": "crashed",
      "success_count": 0,
      "error_count": 0,
      "completed_at": "2026-01-24T12:03:15",
      "error": "Unexpected error: Connection refused to Ollama API"
    }
  },
  "debug_mode": true
}
```

**Backward Compatibility**:
- `from_dict()` は旧形式（list）と新形式（dict）の両方をサポート
- 旧形式の読み込み時は `success_count=0, error_count=0` でデフォルト変換

---

## Data Flow Diagram

```text
┌──────────────────────────────────────────────────────────────────────┐
│ discover_items()                                                      │
│   Input: directory path                                               │
│   Output: ProcessingItem(content=None, source_path=zip_path)          │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ReadZipStep [1:1]                                                     │
│   BEFORE: content=None                                                │
│   AFTER:  content='{"conversations": [...]}' (raw JSON string)        │
│   Metrics: timing_ms, before_chars=0, after_chars=N                   │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ParseConversationsStep [1:N]                                          │
│   BEFORE: content='{"conversations": [{...}, {...}, ...]}' (1 item)   │
│   AFTER:  content=<individual conv dict> (N items)                    │
│   Metrics: timing_ms, before_chars, after_chars (per expanded item)   │
│   Metadata: parent_item_id, expansion_index, total_expanded           │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼ (N items)
┌──────────────────────────────────────────────────────────────────────┐
│ ConvertFormatStep [1:1 each]                                          │
│   BEFORE: content={"uuid": "xxx", "mapping": {...}}                   │
│   AFTER:  content=[{"sender": "human", ...}, ...]                     │
│   Metadata: message_count, format="claude"                            │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ValidateMinMessagesStep [1:1 each]                                    │
│   BEFORE: content=[messages...], status=PENDING                       │
│   AFTER:  status=PENDING or SKIPPED                                   │
│   Metadata: skip_reason (if skipped)                                  │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
                          Transform Stage
```

---

## Relationships

```text
BaseStep <|-- ReadZipStep
BaseStep <|-- ParseConversationsStep
BaseStep <|-- ConvertFormatStep
BaseStep <|-- ValidateMinMessagesStep

BaseStage <|-- ChatGPTExtractor

ChatGPTExtractor --uses--> [ReadZipStep, ParseConversationsStep,
                            ConvertFormatStep, ValidateMinMessagesStep]

ProcessingItem --metadata--> parent_item_id (1:N 展開追跡)
```

---

## Validation Rules Summary

| Entity | Rule | Error Handling |
|--------|------|----------------|
| ReadZipStep | source_path must be ZIP | validate_input returns False |
| ParseConversationsStep | content must be valid JSON array | Yield single FAILED item |
| ConvertFormatStep | content must have 'mapping' key | on_error returns None |
| ValidateMinMessagesStep | message count >= MIN_MESSAGES | status=SKIPPED |
| BaseStep.process() | list return must not be empty | RuntimeError raised |

---

## 6. Debug Output (Stage-level)

**Debug mode only**: `debug_mode=True` の場合に各 Stage の最終結果を JSONL 形式で出力。

```text
Debug Output (Stage-level, DEBUG mode only)
├── item_id: str          # アイテム識別子
└── content: str          # Stage 最終ステップ後のフルコンテンツ（トランケートなし）
```

### 出力タイミング

- 各 Stage の**全ステップ完了後**に1回だけ出力
- 中間ステップの出力はなし（最終結果のみ）

### ファイルフォーマット

**拡張子**: `.jsonl` (JSON Lines)
**書き込みモード**: 追記 (`"a"`)
**ファイル名**: `{source_path.stem}_{stage_type}.jsonl`

**出力先**:
```
{stage.output_path}/debug/{source_path.stem}_{stage_type}.jsonl
```

### データ形式

**1行1JSONオブジェクト** (JSONL):
```jsonl
{"item_id":"conv_uuid_1","content":"[full content after all extract steps]"}
```

**content の優先順位**: `transformed_content` → `content` → `""`

### 出力例

```
.staging/@session/20260124_120000/import/
├── extract/output/debug/
│   └── test_extract.jsonl
│       {"item_id":"conv1","content":"[JSON after ReadZip → Parse → Convert → Validate]"}
├── transform/output/debug/
│   └── test_transform.jsonl
│       {"item_id":"conv1","content":"[Markdown after ExtractKnowledge → GenerateMetadata]"}
└── load/output/debug/
    └── test_load.jsonl
        {"item_id":"conv1","content":"[Final markdown with frontmatter]"}
```

### 特徴

| 特徴 | 説明 |
|------|------|
| **追記式** | 同じファイルに複数回実行した場合、履歴が蓄積される |
| **Stage単位** | extract, transform, load それぞれの最終結果のみ |
| **フルコンテンツ** | トランケートなし、全文保存 |
| **シンプル** | `item_id` と `content` のみ（metadata等は含まない） |

### 用途

- Stage 間の変換内容の確認
- 最終出力の検証
- トラブルシューティング時のデータ追跡
