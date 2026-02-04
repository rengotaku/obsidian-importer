# Extractor Contract

## BaseExtractor Template Method Contract

### `discover_items(input_path: Path, chunk: bool = True) -> Iterator[ProcessingItem]`

**Invariant**: `_discover_raw_items()` が yield した各 item に対して `_chunk_if_needed()` を適用し、結果を yield する。

**Post-condition**: yield される各 ProcessingItem は以下を満たす:
- `item_id` が非空
- `content` が設定済み（プロバイダーがパース完了）
- `metadata` に `source_provider` が設定済み

### `_discover_raw_items(input_path: Path) -> Iterator[ProcessingItem]`

**Contract**: 入力ソースから ProcessingItem を発見して yield する。

**Responsibility**:
- 入力ソースの読み込み（ZIP, JSON, directory, URL）
- データのパース・変換（プロバイダー固有フォーマット → 共通フォーマット）
- `content` フィールドへの設定
- `metadata` への必要情報の設定

**NOT responsible for**:
- チャンキング（`_chunk_if_needed()` が担当）
- JSONL ログ出力（`BaseStage.run()` が担当）
- エラーハンドリング（`BaseStage.run()` が担当）

### `_build_chunk_messages(chunk, conversation_dict) -> list[dict] | None`（新規 hook）

**Contract**: チャンク分割後の `chat_messages` を構築する。

- `None` を返す（デフォルト）: BaseExtractor が `item.content` をそのまま保持
- `list[dict]` を返す: `chunk_conv["chat_messages"]` に設定される

**Rationale**: Claude と ChatGPT で `chat_messages` の dict 構造が異なる（`uuid`/`created_at` の有無）。この差分を hook で吸収し、`_chunk_if_needed()` の override を不要にする。

### `steps` property

**Contract**: `run(ctx, items)` で実行される Step のリスト。

**Invariant**: Steps は **バリデーション・メタデータ付与のみ** を行う。入力読み込み（ZIP, JSON, git clone）やフォーマット変換は `_discover_raw_items()` が担当する。Steps に入力読み込みや変換処理を含めてはならない。

## Extractor Implementation Matrix

| Extractor | discover sets content | Steps role | Chunking | `_build_chunk_messages` |
|-----------|:---:|------------|:---:|:---:|
| ClaudeExtractor | Yes | Validate JSON structure | Yes | `{text, sender}` |
| ChatGPTExtractor | Yes | Validate min messages | Yes | `{uuid, text, sender, created_at}` |
| GitHubExtractor | Yes | Clone + Parse Jekyll + Transform frontmatter | Yes (via template) | None (skip) |
| FileExtractor | No (BaseStage) | Read + Parse frontmatter | N/A | N/A |

## CLI Input Contract

### `--input` (repeatable)

```
--input SOURCE [--input SOURCE ...]
```

- 複数回指定可能（`action="append"`）
- 各 SOURCE は `--input-type` に従って解釈される
- Makefile ではカンマ区切りで指定: `INPUT=a.zip,b.zip`

### `--input-type` (default: `path`)

| Value | Validation | Behavior |
|-------|-----------|----------|
| `path` | `Path.exists()` チェック | ファイル/ディレクトリを `extract/input/` にコピー |
| `url` | URL フォーマットチェック | `extract/input/url.txt` に保存、Extractor が処理 |

**Invariant**: `--input-type` は全 `--input` に適用される（混在不可）。

**Post-condition**: `extract/input/` に入力データが配置され、Extractor が読み取り可能な状態になる。

### 入力バリデーション

| input_type | INPUT 値 | 動作 |
|-----------|---------|------|
| `path`（デフォルト） | ローカルパス | `Path.exists()` チェック → コピー |
| `path` | URL 文字列 | **エラー**: `Path does not exist` |
| `url` | URL 文字列 | URL フォーマットチェック → `url.txt` 保存 |
| `url` | ローカルパス | **エラー**: `Invalid URL format` |
