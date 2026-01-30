# Research: チャンク処理の共通化

**Feature**: 035-chunking-mixin
**Date**: 2026-01-26

## 調査項目

### 1. 既存 Extractor のチャンク処理実装状況

| Extractor | チャンク処理 | 実装場所 |
|-----------|------------|---------|
| ClaudeExtractor | ✅ あり | `_expand_conversations()` + `_chunk_conversation()` |
| ChatGPTExtractor | ❌ なし | `discover_items()` は ZIP 発見のみ |
| GitHubExtractor | ❌ なし | `discover_items()` はファイル発見のみ |

**Decision**: ClaudeExtractor のチャンク処理を基盤に、他の Extractor へ展開

**Rationale**: 既に動作実績があり、Chunker クラスが Protocol-based で設計されている

**Alternatives considered**:
- 各 Extractor に個別実装 → コード重複、機能漏れリスク
- 外部ライブラリ導入 → 不要な依存追加

### 2. 現在のアーキテクチャ分析

#### BaseStage の責務

```
BaseStage (ABC)
├── stage_type [abstract property]
├── steps [abstract property]
├── run() - アイテム処理ループ
└── _process_item() - Step 実行
```

**発見**: `discover_items()` は BaseStage に定義されていない。各 Extractor が独自実装。

#### discover_items() のパターン

| Extractor | discover_items() の役割 |
|-----------|------------------------|
| ClaudeExtractor | JSON パース + チャンク分割 + ProcessingItem 生成 |
| ChatGPTExtractor | ZIP 発見のみ（Steps で処理） |
| GitHubExtractor | git clone + ファイル発見 |

**Decision**: Template Method パターンを BaseStage に追加

**Rationale**:
- `discover_items()` を BaseStage の concrete method に
- `_discover_raw_items()` を abstract method に（各プロバイダー実装）
- `_chunk_if_needed()` を BaseStage の protected method に（自動適用）

**Alternatives considered**:
- Mixin パターン → 3つの失敗ポイント（継承忘れ、init 忘れ、呼び出し忘れ）
- Decorator パターン → 実行時オーバーヘッド、デバッグ困難

### 3. Chunker クラスの再利用性

```python
class Chunker:
    def should_chunk(self, conversation: ConversationProtocol) -> bool
    def split(self, conversation: ConversationProtocol) -> ChunkResult
    def get_chunk_filename(self, base_name: str, chunk: Chunk, result: ChunkResult) -> str
```

**ConversationProtocol**:
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

**Decision**: ConversationProtocol を各プロバイダーが実装

**Rationale**: Protocol-based 設計により、型安全にチャンク処理を統一できる

### 4. ChatGPT/GitHub でのチャンク処理追加箇所

#### ChatGPTExtractor

現状: Steps ベースの処理パイプライン
```
discover_items() → [ZIP発見]
Steps: ReadZipStep → ParseConversationsStep → ExpandConversationsStep → ...
```

**課題**: `ExpandConversationsStep` でチャンク処理が必要

**Decision**: Step レベルではなく、`_discover_raw_items()` + BaseStage で処理

**Rationale**:
- ClaudeExtractor と同じパターンに統一
- Steps は変換処理に集中

#### GitHubExtractor

現状: ファイル単位で ProcessingItem 生成
```
discover_items() → [git clone + glob]
```

**課題**: Jekyll 記事が大きい場合のチャンク処理

**Decision**: GitHub コンテンツはチャンク対象外（記事単位で完結）

**Rationale**:
- ブログ記事は通常 25,000 文字未満
- メッセージ構造がないためチャンク分割の意味が薄い
- `_build_conversation_for_chunking()` で "チャンク不要" を返す

### 5. CLI オプション設計

**Decision**: `--chunk` オプションでチャンク分割を有効化（デフォルト無効）

**Rationale**:
- デフォルトでチャンク無効（シンプルな動作）
- 閾値超過ファイルは LLM スキップ + `too_large: true` で明示
- 大きなファイルを分割処理したい場合は `--chunk` でオプトイン
- 後から手動で大きなファイルを確認・対応可能

**Alternatives considered**:
- `--no-chunk` でオプトアウト → デフォルト有効は複雑な動作がデフォルトになる
- `--chunk-size N` → 現状は固定値で十分

## 技術的決定

### Template Method パターン実装

```python
# BaseStage に追加
def discover_items(self, input_path: Path, *, no_chunk: bool = False) -> Iterator[ProcessingItem]:
    """Template method for item discovery with automatic chunking."""
    for item in self._discover_raw_items(input_path):
        if no_chunk:
            yield item
        else:
            yield from self._chunk_if_needed(item)

@abstractmethod
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    """Provider-specific raw item discovery."""
    ...

def _chunk_if_needed(self, item: ProcessingItem) -> Iterator[ProcessingItem]:
    """Apply chunking if item exceeds threshold."""
    conversation = self._build_conversation_for_chunking(item)
    if conversation is None:
        yield item
        return

    if not self._chunker.should_chunk(conversation):
        yield item
        return

    # Chunk and yield multiple items
    ...

@abstractmethod
def _build_conversation_for_chunking(self, item: ProcessingItem) -> ConversationProtocol | None:
    """Build ConversationProtocol for chunking. Return None if not applicable."""
    ...
```

### 抽象メソッド強制の検証

Python の ABC は、抽象メソッド未実装でインスタンス化時に `TypeError` を発生させる。

```python
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def required_method(self): ...

class Incomplete(Base):
    pass  # required_method 未実装

# Incomplete() → TypeError: Can't instantiate abstract class Incomplete with abstract method required_method
```

**確認済み**: SC-006（TypeError on missing abstract method）は Python 標準機能で達成可能。

## 未解決事項

なし - 全ての NEEDS CLARIFICATION を解決。
