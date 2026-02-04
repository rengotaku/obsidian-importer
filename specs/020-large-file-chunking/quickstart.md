# Quickstart: 大規模ファイルのチャンク分割処理

**Date**: 2026-01-17
**Feature**: 020-large-file-chunking

## Overview

大規模な会話ファイル（25,000文字以上）を自動的にチャンク分割し、各チャンクを個別に LLM 処理して連番付きファイルとして出力する機能。

## Usage

### 既存コマンド（変更なし）

```bash
# 通常のインポート処理（チャンク分割は自動）
make import-claude

# プロセス実行
make process SESSION=import_20260117_123456
```

チャンク分割は `KnowledgeExtractor.extract()` 内部で自動的に行われるため、ユーザーの操作は変わらない。

### ログ出力例

```
Processing: 長い会話タイトル.md
  → チャンク分割: 3 チャンク（総文字数: 85,000）
  → チャンク 1/3 処理中...
  → チャンク 1/3 完了 → 長い会話タイトル_001.md
  → チャンク 2/3 処理中...
  → チャンク 2/3 完了 → 長い会話タイトル_002.md
  → チャンク 3/3 処理中...
  → チャンク 3/3 完了 → 長い会話タイトル_003.md
  ✓ 成功 (3 ファイル出力)
```

## Configuration

### チャンクサイズ

デフォルト: 25,000 文字

環境変数で変更可能（将来対応予定）:

```bash
export LLM_IMPORT_CHUNK_SIZE=30000
```

### オーバーラップ

デフォルト: 2 メッセージ

## API (Internal)

### Chunker クラス

```python
from scripts.llm_import.common.chunker import Chunker

chunker = Chunker(chunk_size=25000, overlap_messages=2)

# チャンク分割が必要か判定
if chunker.should_chunk(conversation):
    chunked = chunker.split(conversation)
    print(f"チャンク数: {len(chunked.chunks)}")
```

### KnowledgeExtractor 拡張

```python
from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor

extractor = KnowledgeExtractor()

# extract() はチャンク分割を内部で自動処理
result = extractor.extract(large_conversation)
# result.document は統合済みの KnowledgeDocument
```

## Testing

```bash
# ユニットテスト
make test

# チャンク分割のみテスト
python -m unittest development/scripts/llm_import/tests/test_chunker.py
```

## Troubleshooting

### Q: チャンク処理が遅い

- 各チャンクで LLM API を呼び出すため、チャンク数に比例して時間がかかる
- 目安: 1 チャンク ≈ 30〜60 秒
- 3 チャンクの会話 → 約 2〜3 分

### Q: 一部チャンクが失敗した

- 失敗チャンクは自動で 2 回までリトライ
- 全リトライ失敗 → エラーファイルに記録
- `make retry` で再処理可能

### Q: 同じ内容が複数ファイルに出力される

- オーバーラップ領域から類似内容が抽出されることがある
- 各チャンクは独立ファイルなので、重複除去はしない
- 必要に応じて手動で統合・編集
