# Data Model: チャンク処理の共通化

**Feature**: 035-chunking-mixin
**Date**: 2026-01-26

## Entity Diagram

```
                    BaseStage (ABC)
                         │
                         │ Template Method
                         ▼
            ┌────────────────────────────┐
            │      discover_items()      │ ← Concrete (template method)
            │  ┌──────────────────────┐  │
            │  │ _discover_raw_items()│  │ ← Abstract (provider impl)
            │  └──────────┬───────────┘  │
            │             │              │
            │             ▼              │
            │  ┌──────────────────────┐  │
            │  │  _chunk_if_needed()  │  │ ← Concrete (auto apply)
            │  └──────────┬───────────┘  │
            │             │              │
            │             ▼              │
            │  ┌──────────────────────┐  │
            │  │ _build_conversation_ │  │ ← Abstract (provider impl)
            │  │   for_chunking()     │  │
            │  └──────────────────────┘  │
            └────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ClaudeExtractor│ │ChatGPTExtractor│ │GitHubExtractor│
└─────────────┘  └─────────────┘  └─────────────┘
```

## Entities

### BaseStage (拡張)

既存の BaseStage クラスに Template Method パターンを追加。

| Field/Method | Type | Description |
|--------------|------|-------------|
| `_chunker` | `Chunker` | チャンク分割インスタンス |
| `discover_items()` | Method | Template method - チャンク処理を自動適用 |
| `_discover_raw_items()` | Abstract | プロバイダー固有のアイテム発見 |
| `_chunk_if_needed()` | Method | チャンク判定・分割 |
| `_build_conversation_for_chunking()` | Abstract | ConversationProtocol への変換 |

**Validation Rules**:
- `_discover_raw_items()` 未実装 → `TypeError` at instantiation
- `_build_conversation_for_chunking()` 未実装 → `TypeError` at instantiation

### ProcessingItem (既存、metadata 拡張)

チャンク処理時に追加される metadata フィールド。

| Metadata Field | Type | Description |
|----------------|------|-------------|
| `is_chunked` | `bool` | チャンク分割されたかどうか |
| `parent_item_id` | `str \| None` | 親アイテムの item_id（チャンク時のみ） |
| `chunk_index` | `int \| None` | チャンクインデックス（0-based） |
| `total_chunks` | `int \| None` | 総チャンク数 |
| `too_large` | `bool` | 閾値超過でスキップされたかどうか（frontmatter に出力） |

### ConversationProtocol (既存)

チャンク判定に必要なインターフェース。

```python
@runtime_checkable
class ConversationProtocol(Protocol):
    @property
    def messages(self) -> list[MessageProtocol]: ...

    @property
    def id(self) -> str: ...

    @property
    def provider(self) -> str: ...
```

### Chunker (既存)

チャンク分割ロジック。変更なし。

| Method | Description |
|--------|-------------|
| `should_chunk(conversation)` | 閾値超過判定 |
| `split(conversation)` | チャンク分割実行 |
| `get_chunk_filename(base, chunk, result)` | ファイル名生成 |

**定数**:
- `CHUNK_SIZE`: 25,000 文字（デフォルト）
- `OVERLAP_MESSAGES`: 2 件（文脈維持用）

## State Transitions

### ProcessingItem Status

```
[discover_items()] → PENDING
        │
        ├─ (chunking) → [multiple items] → PENDING (each)
        │
        └─ (no chunking) → PENDING
                │
                ▼
        [Steps processing]
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
   COMPLETED  FAILED  SKIPPED
```

### Chunk Metadata Flow

```
Original Item (is_chunked=false, parent_item_id=null)
        │
        │ _chunk_if_needed() → should_chunk=true
        ▼
┌──────────────────────────────────────────────────┐
│  Chunk 0: is_chunked=true, parent_item_id=X,     │
│           chunk_index=0, total_chunks=N          │
├──────────────────────────────────────────────────┤
│  Chunk 1: is_chunked=true, parent_item_id=X,     │
│           chunk_index=1, total_chunks=N          │
├──────────────────────────────────────────────────┤
│  ...                                             │
├──────────────────────────────────────────────────┤
│  Chunk N-1: is_chunked=true, parent_item_id=X,   │
│             chunk_index=N-1, total_chunks=N      │
└──────────────────────────────────────────────────┘
```

## Provider-Specific Implementations

### ClaudeExtractor

```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    """Parse conversations.json and yield items."""
    # 既存の _expand_conversations() ロジックを移植
    # チャンク処理は BaseStage に委譲

def _build_conversation_for_chunking(self, item: ProcessingItem) -> ConversationProtocol | None:
    """Convert Claude conversation JSON to ConversationProtocol."""
    # 既存の _build_conversation_for_chunking() をそのまま使用
```

### ChatGPTExtractor

```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    """Find ZIP, extract, parse conversations.json, yield items."""
    # 現在 Steps で行っている処理を discover_items レベルに移動

def _build_conversation_for_chunking(self, item: ProcessingItem) -> ConversationProtocol | None:
    """Convert ChatGPT conversation to ConversationProtocol."""
    # ChatGPT の mapping 構造を ConversationProtocol に変換
```

### GitHubExtractor

```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    """Clone repo and yield markdown files."""
    # 既存ロジックをそのまま使用

def _build_conversation_for_chunking(self, item: ProcessingItem) -> ConversationProtocol | None:
    """GitHub articles don't need chunking."""
    return None  # チャンク処理をスキップ
```

## Validation Rules

| Rule | Scope | Enforcement |
|------|-------|-------------|
| Abstract method 実装必須 | Class | `TypeError` at instantiation |
| `_discover_raw_items()` は Iterator を返す | Method | Type hint + runtime check |
| `_build_conversation_for_chunking()` は Protocol または None | Method | Type hint |
| チャンク閾値 > 0 | Config | Chunker 初期化時チェック |
| チャンク結果 >= 1 アイテム | Runtime | `RuntimeError` if empty |

## Relationships

```
BaseStage 1 ──── * ProcessingItem (yields)
BaseStage 1 ──── 1 Chunker (has)

ProcessingItem 1 ──── 0..1 ProcessingItem (parent_item_id)

ConversationProtocol * ──── 1 Chunker (uses)
```
