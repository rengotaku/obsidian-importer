# Chunker Interface Contract

**Date**: 2026-01-17
**Module**: `development/scripts/llm_import/common/chunker.py`

## Public Interface

### Class: Chunker

```python
class Chunker:
    """
    会話をチャンクに分割するユーティリティクラス。

    メッセージ境界で分割し、文脈維持のためオーバーラップを設ける。
    """

    def __init__(
        self,
        chunk_size: int = 25000,
        overlap_messages: int = 2,
    ) -> None:
        """
        Args:
            chunk_size: チャンクサイズ閾値（文字数）
            overlap_messages: オーバーラップするメッセージ数
        """

    def should_chunk(self, conversation: BaseConversation) -> bool:
        """
        チャンク分割が必要か判定。

        Args:
            conversation: 会話データ

        Returns:
            True: 総文字数 >= chunk_size
            False: チャンク分割不要
        """

    def split(self, conversation: BaseConversation) -> ChunkedConversation:
        """
        会話をチャンクに分割。

        Args:
            conversation: 元の会話データ

        Returns:
            ChunkedConversation: 分割結果

        Raises:
            ValueError: 会話が空の場合
        """

    @staticmethod
    def get_chunk_filename(title: str, chunk_index: int) -> str:
        """
        チャンク用ファイル名を生成。

        Args:
            title: 元の会話タイトル
            chunk_index: チャンク番号（0-indexed）

        Returns:
            連番付きファイル名（例: "タイトル_001.md"）
        """
```

## Data Contracts

### Input: BaseConversation

```python
# 既存の BaseConversation を使用
# development/scripts/llm_import/base.py

@dataclass
class BaseConversation:
    id: str
    title: str
    created_at: str
    messages: list[Message]
    provider: str
    summary: str | None = None
```

### Output: ChunkedConversation

```python
@dataclass
class ChunkedConversation:
    original: BaseConversation    # 元の会話
    chunks: list[Chunk]           # チャンクリスト
    total_chars: int              # 元の総文字数
    chunk_size: int               # 使用したチャンクサイズ
```

### Output: Chunk

```python
@dataclass
class Chunk:
    index: int                    # チャンク番号（0-indexed）
    messages: list[Message]       # メッセージリスト
    char_count: int              # 文字数
    has_overlap: bool            # オーバーラップ有無
    overlap_count: int           # オーバーラップ数
```

### Input/Output: ChunkResult

```python
@dataclass
class ChunkResult:
    chunk_index: int              # チャンク番号
    success: bool                 # 成功/失敗
    summary: str | None           # サマリー
    learnings: list[str]          # 学び
    code_snippets: list[CodeSnippet]  # コード
    error: str | None             # エラー
    raw_response: str | None      # 生レスポンス
```

## Behavior Contracts

### should_chunk()

| Condition | Return |
|-----------|--------|
| `sum(len(m.content) for m in messages) >= chunk_size` | True |
| Otherwise | False |

### split()

1. メッセージを順に走査
2. 累積文字数が `chunk_size` を超えたらチャンク境界
3. 次チャンクは前チャンクの末尾 `overlap_messages` 個を含む
4. 空チャンクは生成しない

### get_chunk_filename()

```python
get_chunk_filename("長い会話", 0) → "長い会話_001.md"
get_chunk_filename("長い会話", 1) → "長い会話_002.md"
get_chunk_filename("長い会話", 9) → "長い会話_010.md"
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| 空の会話 | `ValueError` |
| 単一メッセージ > chunk_size | 1 チャンクとして処理（警告ログ） |
| チャンク処理失敗 | エラーファイルに記録、他チャンクは継続 |
