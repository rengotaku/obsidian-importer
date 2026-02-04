# Quickstart: チャンク処理の共通化

**Feature**: 035-chunking-mixin
**Date**: 2026-01-26

## 概要

全 Extractor（Claude, ChatGPT, GitHub）で大きな会話を自動的にチャンク分割する機能。Template Method パターンにより、新規プロバイダー追加時の機能漏れを防止。

## 使用方法

### 基本（チャンク無効 - デフォルト）

```bash
# Claude インポート（チャンク無効 - デフォルト）
make import INPUT=~/.staging/@llm_exports/claude/

# ChatGPT インポート（チャンク無効 - デフォルト）
make import INPUT=chatgpt_export.zip PROVIDER=openai

# GitHub インポート（チャンク対象外 - 記事単位）
make import INPUT=https://github.com/user/repo/tree/master/_posts PROVIDER=github
```

**デフォルト動作**:
- チャンク分割は無効
- 25,000 文字を超えるファイルは LLM 処理をスキップ
- スキップされたファイルは `status=SKIPPED`、frontmatter に `too_large: true` を追記
- 後続のアイテムは正常に処理継続

### チャンク有効化

```bash
# チャンク分割有効化（大きな会話を分割して処理）
make import INPUT=... CHUNK=1
python -m src.etl import --input ... --chunk
```

**`--chunk` の動作**:
- チャンク分割を有効化
- 25,000 文字を超えるファイルは複数のチャンクに分割
- 各チャンクが個別に LLM 処理される

## 新規プロバイダー実装ガイド

### 1. 必須メソッド実装

```python
from src.etl.core.stage import BaseStage
from src.etl.utils.chunker import ConversationProtocol

class NewProviderExtractor(BaseStage):
    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Required: Raw item discovery without chunking."""
        # 入力ファイルを読み込み、ProcessingItem を yield
        for file in input_path.glob("*.json"):
            yield ProcessingItem(
                item_id=generate_file_id(...),
                source_path=file,
                content=file.read_text(),
                ...
            )

    def _build_conversation_for_chunking(
        self, item: ProcessingItem
    ) -> ConversationProtocol | None:
        """Required: Convert to ConversationProtocol for chunking."""
        # チャンク不要の場合は None を返す
        if not self._needs_chunking(item):
            return None

        # ConversationProtocol を実装したオブジェクトを返す
        return MyConversation(
            messages=[...],
            id=item.item_id,
            provider="new_provider",
        )
```

### 2. ConversationProtocol 実装

```python
from dataclasses import dataclass
from src.etl.utils.chunker import ConversationProtocol, MessageProtocol

@dataclass
class MyMessage:
    role: str
    text: str

    @property
    def content(self) -> str:
        return self.text

@dataclass
class MyConversation:
    messages: list[MyMessage]
    id: str
    provider: str = "new_provider"
```

### 3. 抽象メソッド未実装時のエラー

```python
class IncompleteExtractor(BaseStage):
    # _discover_raw_items() を実装しない

# インスタンス化時に TypeError
IncompleteExtractor()
# TypeError: Can't instantiate abstract class IncompleteExtractor
#            with abstract methods _build_conversation_for_chunking, _discover_raw_items
```

## チャンク処理フロー

```
                    ┌─────────────────────────┐
                    │    discover_items()     │
                    │   (BaseStage - auto)    │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  _discover_raw_items()  │
                    │  (Provider - required)  │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  --chunk オプション？   │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
    ┌──────────────────┐               ┌──────────────────┐
    │  --chunk なし    │               │  --chunk あり    │
    │  (デフォルト)    │               │                  │
    └────────┬─────────┘               └────────┬─────────┘
             │                                   │
             ▼                                   ▼
    ┌──────────────────┐               ┌──────────────────┐
    │ chars <= 25,000  │               │ _chunk_if_needed │
    │   → LLM処理      │               │   (BaseStage)    │
    ├──────────────────┤               └────────┬─────────┘
    │ chars > 25,000   │                        │
    │   → SKIPPED      │               ┌────────┴────────┐
    │   too_large:true │               │                 │
    └──────────────────┘               ▼                 ▼
                                 chars<=25k        chars>25k
                                 (1:1出力)         (1:N出力)
```

## チャンク metadata

```python
# チャンク分割されたアイテムの metadata
{
    "is_chunked": True,
    "parent_item_id": "abc123",  # 元アイテムの item_id
    "chunk_index": 0,            # 0-based インデックス
    "total_chunks": 12,          # 総チャンク数
    ...
}
```

## 設定値

| 設定 | 値 | 説明 |
|------|-----|------|
| `CHUNK_SIZE` | 25,000 | チャンク分割閾値（文字数） |
| `OVERLAP_MESSAGES` | 2 | 文脈維持用オーバーラップメッセージ数 |

## テスト実行

```bash
# ユニットテスト
make test

# 大きな会話を含むインポートテスト
make import INPUT=... DEBUG=1 LIMIT=5
```

## トラブルシューティング

### チャンク分割されない

1. `--chunk` オプションが指定されていない（デフォルトは無効）
2. 会話の総文字数が 25,000 以下
3. `_build_conversation_for_chunking()` が `None` を返している

### TypeError at instantiation

新規プロバイダーで抽象メソッドが未実装:
- `_discover_raw_items()` を実装する
- `_build_conversation_for_chunking()` を実装する

### 大きな会話がスキップされる

1. デフォルト動作では閾値超過ファイルは LLM スキップ
2. 分割処理したい場合は `--chunk` を指定
3. スキップされたファイルは frontmatter に `too_large: true` が付与される

### 大きな会話がタイムアウト（`--chunk` 指定時）

1. Ollama のタイムアウト設定を確認
2. チャンクサイズ閾値（25,000 文字）が適切か確認
