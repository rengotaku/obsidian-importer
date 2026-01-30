# Data Model: 大規模ファイルのチャンク分割処理

**Date**: 2026-01-17
**Feature**: 020-large-file-chunking

## Entities

### Chunk

分割された会話の一部分を表すデータクラス。

```python
@dataclass
class Chunk:
    """チャンク（分割された会話の一部）"""
    index: int                    # チャンク番号（0-indexed）
    messages: list[Message]       # このチャンクに含まれるメッセージ
    char_count: int              # 文字数
    has_overlap: bool            # 前チャンクからのオーバーラップを含むか
    overlap_count: int           # オーバーラップメッセージ数
```

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| index | int | チャンク番号 | >= 0 |
| messages | list[Message] | メッセージリスト | len >= 1 |
| char_count | int | 総文字数 | > 0 |
| has_overlap | bool | オーバーラップ有無 | - |
| overlap_count | int | オーバーラップ数 | >= 0 |

### ChunkResult

各チャンクの LLM 処理結果。

```python
@dataclass
class ChunkResult:
    """チャンク処理結果"""
    chunk_index: int              # 処理したチャンク番号
    success: bool                 # 成功/失敗
    summary: str | None           # サマリー（成功時）
    learnings: list[str]          # 学び（成功時）
    code_snippets: list[CodeSnippet]  # コードスニペット（成功時）
    error: str | None             # エラーメッセージ（失敗時）
    raw_response: str | None      # LLM 生レスポンス
```

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| chunk_index | int | チャンク番号 | >= 0 |
| success | bool | 処理成功フラグ | - |
| summary | str \| None | チャンクサマリー | success=True 時必須 |
| learnings | list[str] | 学びリスト | success=True 時必須 |
| code_snippets | list[CodeSnippet] | コード | success=True 時空可 |
| error | str \| None | エラー | success=False 時必須 |
| raw_response | str \| None | 生レスポンス | デバッグ用 |

### ChunkedConversation

チャンク分割された会話全体を表す。

```python
@dataclass
class ChunkedConversation:
    """チャンク分割された会話"""
    original: BaseConversation    # 元の会話
    chunks: list[Chunk]           # チャンクリスト
    total_chars: int              # 元の総文字数
    chunk_size: int               # 使用したチャンクサイズ閾値
```

## Relationships

```
BaseConversation (既存)
    │
    ├── 1:N ──► Chunk
    │              │
    │              └── 1:1 ──► ChunkResult
    │
    └── 1:1 ──► ChunkedConversation
                   │
                   └── 1:N ──► Chunk
```

## State Transitions

### Chunk Processing States

```
[Created] ──► [Processing] ──► [Success]
                  │
                  └──────────► [Failed] ──► [Retrying] ──► [Success]
                                                │
                                                └──────────► [Failed]
```

| State | Description |
|-------|-------------|
| Created | チャンク生成済み、未処理 |
| Processing | LLM 処理中 |
| Success | 処理成功、結果取得済み |
| Failed | 処理失敗 |
| Retrying | リトライ中 |

## Integration with Existing Models

### BaseConversation (既存)

```python
# development/scripts/llm_import/base.py
@dataclass
class BaseConversation:
    id: str
    title: str
    created_at: str
    messages: list[Message]
    provider: str
    # ... other fields
```

### KnowledgeDocument (既存)

```python
# development/scripts/llm_import/common/knowledge_extractor.py
@dataclass
class KnowledgeDocument:
    title: str
    summary: str
    learnings: list[str]
    code_snippets: list[CodeSnippet]
    # ... other fields
```

## Chunker Module Interface

```python
class Chunker:
    """会話をチャンクに分割"""

    def __init__(
        self,
        chunk_size: int = 25000,
        overlap_messages: int = 2,
    ) -> None: ...

    def should_chunk(self, conversation: BaseConversation) -> bool:
        """チャンク分割が必要か判定"""
        ...

    def split(self, conversation: BaseConversation) -> ChunkedConversation:
        """会話をチャンクに分割"""
        ...

    @staticmethod
    def get_chunk_filename(title: str, chunk_index: int) -> str:
        """チャンク用ファイル名を生成（例: タイトル_001.md）"""
        ...
```
