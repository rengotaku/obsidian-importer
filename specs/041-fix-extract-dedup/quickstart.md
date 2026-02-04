# Quickstart: 重複処理の解消

## 概要

BaseExtractor テンプレートを完成させ、構造的に重複が不可能な設計にする。
修正対象ファイル一覧は [plan.md](./plan.md) の Project Structure を参照。

## 修正パターン

### 1. BaseExtractor テンプレート完成

```python
class BaseExtractor(BaseStage):
    # _build_chunk_messages: 新規 hook
    def _build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict] | None:
        """チャンク分割後の chat_messages を構築する（子クラスが override）。
        None を返すと item.content をそのまま使用。"""
        return None

    def _chunk_if_needed(self, item):
        # ... 既存のチャンク判定 ...
        for chunk_idx, chunk in enumerate(chunked.chunks):
            chunk_conv = dict(conv)
            # hook で messages を構築
            messages = self._build_chunk_messages(chunk, chunk_conv)
            if messages is not None:
                chunk_conv["chat_messages"] = messages
            chunk_content = json.dumps(chunk_conv, ensure_ascii=False)
            # ... ProcessingItem 生成 ...
```

### 2. 子クラスは hook のみ実装

```python
# Claude
def _build_chunk_messages(self, chunk, conv_dict):
    return [{"text": msg.content, "sender": msg.role} for msg in chunk.messages]

# ChatGPT
def _build_chunk_messages(self, chunk, conv_dict):
    return [
        {"uuid": "", "text": msg.content, "sender": msg.role,
         "created_at": conv_dict.get("created_at", "")}
        for msg in chunk.messages
    ]
```

### 3. ChatGPT Steps: 重複処理削除

```python
# BEFORE: 4 Steps (ReadZip, ParseConversations, ConvertFormat, ValidateMinMessages)
# AFTER:  1 Step  (ValidateMinMessages のみ)

class ChatGPTExtractor(BaseExtractor):
    @property
    def steps(self):
        return [ValidateMinMessagesStep()]
```

### 4. 冗長 override 削除

```python
# BEFORE: 各子クラスで stage_type を再定義
class ClaudeExtractor(BaseExtractor):
    @property
    def stage_type(self):
        return StageType.EXTRACT  # ← BaseExtractor と同値

# AFTER: 削除（BaseExtractor から継承）
```

### 5. GitHub discover_items() override 削除

```python
# BEFORE
class GitHubExtractor(BaseExtractor):
    def discover_items(self, input_source):  # ← テンプレートをバイパス
        ...
    def _discover_raw_items(self, input_path):
        ...

# AFTER: _discover_raw_items() のみ（BaseExtractor テンプレート使用）
```

## テスト実行

```bash
make test  # 全テスト（回帰確認含む）
```

## 検証方法

```bash
# ChatGPT インポートで重複が発生しないことを確認
make import INPUT=chatgpt_export.zip PROVIDER=openai LIMIT=5 DEBUG=1

# Extract 出力のレコード数確認
wc -l .staging/@session/*/import/extract/output/*.jsonl
```

## 入力インターフェース

### INPUT_TYPE 指定

```bash
# ローカルパス（INPUT_TYPE=path がデフォルト）
make import INPUT=./data PROVIDER=claude

# URL 入力（INPUT_TYPE=url を明示指定）
make import INPUT=https://github.com/user/repo/tree/master/_posts INPUT_TYPE=url PROVIDER=github

# 複数入力（カンマ区切り）
make import INPUT=export1.zip,export2.zip PROVIDER=openai
```

### argparse

```python
parser.add_argument("--input", action="append", help="...")
parser.add_argument("--input-type", default="path", choices=["path", "url"])
```
