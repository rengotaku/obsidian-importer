# Data Model: Extract Stage Discovery 委譲

**Date**: 2026-01-23
**Feature**: 031-extract-discovery-delegation

## Overview

本機能は新しいデータモデルを導入しない。既存の ProcessingItem を使用する。

## Existing Entities

### ProcessingItem

パイプラインを通過するデータ単位。変更なし。

```python
@dataclass
class ProcessingItem:
    item_id: str                    # ファイル ID（SHA256 ハッシュ）
    source_path: Path              # 元ファイルパス
    current_step: str              # 現在のステップ名
    status: ItemStatus             # 処理状態
    content: str | None            # 会話コンテンツ（JSON）
    transformed_content: str | None # 変換後コンテンツ
    metadata: dict                 # メタデータ
    error: str | None              # エラーメッセージ
```

### メタデータ構造

discover_items() が設定するメタデータ（変更なし）:

```python
metadata = {
    "discovered_at": str,           # ISO 形式タイムスタンプ
    "source_type": "conversation",  # 固定値
    "conversation_name": str,       # 会話タイトル
    "conversation_uuid": str,       # 会話 UUID
    "created_at": str,              # 作成日時
    "updated_at": str,              # 更新日時
    "source_provider": str,         # "claude" | "openai"
    "is_chunked": bool,             # チャンク分割されたか
    "chunk_index": int | None,      # チャンクインデックス
    "total_chunks": int | None,     # 総チャンク数
    "parent_item_id": str | None,   # 親アイテム ID
}
```

## Interface Changes

### ClaudeExtractor

新規メソッド追加:

```python
class ClaudeExtractor(BaseStage):
    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Claude エクスポートから会話を発見する。"""
        ...

    def _expand_conversations(self, json_file: Path) -> Iterator[ProcessingItem]:
        """conversations.json を展開する。"""
        ...

    def _build_conversation_for_chunking(self, conv: dict) -> SimpleConversation:
        """チャンキング用の会話オブジェクトを構築する。"""
        ...

    def _chunk_conversation(self, conv: dict, ...) -> Iterator[ProcessingItem]:
        """大きな会話をチャンクに分割する。"""
        ...
```

### ImportPhase

変更メソッド:

```python
class ImportPhase:
    def run(self, phase_data, debug_mode=False, limit=None) -> PhaseResult:
        """Extract stage の discover_items() を使用するように変更。"""
        extract_stage = self.create_extract_stage()
        items = extract_stage.discover_items(input_path)  # 変更点
        extracted = extract_stage.run(ctx, items)
        ...
```

削除メソッド:
- `discover_items()`
- `_expand_conversations()`
- `_build_conversation_for_chunking()`
- `_chunk_conversation()`

## No Schema Changes

- データベーススキーマ: 該当なし（ファイルベース）
- 外部 API: 変更なし
- ファイルフォーマット: 変更なし
