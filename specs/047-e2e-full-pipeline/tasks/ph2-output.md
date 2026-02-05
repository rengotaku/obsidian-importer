# Phase 2 Output - User Story 4: パイプライン変更: Vault 書き込み廃止

## 作業概要

- Phase 2 - User Story 4 の実装完了
- FAIL テスト 8 件を PASS させた
- `extract_topic` および `embed_frontmatter_fields` ノードを実装
- Organize パイプラインから Vault 書き込みを廃止
- 振り分け情報（genre, topic）を frontmatter に埋め込む方式に変更

## 修正ファイル一覧

### 実装ファイル

- `src/obsidian_etl/pipelines/organize/nodes.py`
  - `extract_topic()` 関数を追加: LLM で topic 抽出 + 小文字正規化
  - `_extract_topic_via_llm()` ヘルパー関数を追加: Ollama API 呼び出し
  - `embed_frontmatter_fields()` 関数を追加: genre, topic, summary を frontmatter に埋め込み
  - `_embed_fields_in_frontmatter()` ヘルパー関数を追加: frontmatter 更新処理
  - import に `json`, `requests` を追加

- `src/obsidian_etl/pipelines/organize/pipeline.py`
  - `extract_topic` ノードを追加（classify_genre の後）
  - `embed_frontmatter_fields` ノードを追加（clean_content の後）
  - `determine_vault_path` および `move_to_vault` ノードを削除
  - Pipeline フロー: classify → extract_topic → normalize → clean → embed

- `conf/base/catalog.yml`
  - `topic_extracted_items` データセットを追加
  - `organized_notes` データセットを追加（TextDataset, .md suffix）

### テストファイル（統合テスト更新）

- `tests/test_integration.py`
  - `test_import_claude_node_names`: 期待ノード名を更新（determine_vault_path/move_to_vault → extract_topic/embed_frontmatter_fields）
  - `test_import_openai_node_names`: 同上
  - `test_import_github_node_names`: 同上

- `tests/test_pipeline_registry.py`
  - `test_import_claude_contains_organize_nodes`: 期待 organize ノード名を更新

## テスト結果

### 新規テスト（8件）

```
$ .venv/bin/python -m unittest tests.pipelines.organize.test_nodes.TestExtractTopic tests.pipelines.organize.test_nodes.TestEmbedFrontmatterFields

........
----------------------------------------------------------------------
Ran 8 tests in 0.003s

OK
```

**PASS したテスト:**
1. `test_extract_topic_normalizes_to_lowercase`: "AWS" → "aws" に正規化
2. `test_extract_topic_preserves_spaces`: "React Native" → "react native"（スペース保持）
3. `test_extract_topic_empty_on_failure`: LLM 抽出失敗時に空文字
4. `test_embed_frontmatter_fields_adds_genre`: genre が frontmatter に追加
5. `test_embed_frontmatter_fields_adds_topic`: topic が frontmatter に追加
6. `test_embed_frontmatter_fields_adds_empty_topic`: 空 topic が frontmatter に追加（空許容）
7. `test_embed_frontmatter_fields_adds_summary`: summary が frontmatter に追加
8. `test_embed_frontmatter_fields_no_file_write`: ファイルシステム書き込みなし

### Organize パイプライン全テスト（40件）

```
$ .venv/bin/python -m unittest tests.pipelines.organize.test_nodes

........................................
----------------------------------------------------------------------
Ran 40 tests in 0.006s

OK
```

### 全テスト実行結果

- Organize パイプライン関連: **全テスト PASS**
- 統合テスト: **全テスト PASS**
- 既知の RAG 関連エラー: 35 件（Phase 2 の変更とは無関係）

## 実装の詳細

### extract_topic ノード

```python
def extract_topic(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Extract topic from content using LLM.

    - LLM で会話内容から topic を抽出
    - 小文字に正規化 (AWS → aws)
    - スペースは保持 (React Native → react native)
    - 抽出失敗時は空文字
    """
```

**正規化ルール:**
- `topic.lower()` で小文字化
- スペースは保持（`React Native` → `react native`）
- 抽出失敗（`None` または空文字）→ 空文字

**LLM 呼び出し:**
- Ollama API 使用（`params:organize.ollama` から設定取得）
- プロンプト: 会話内容から主題を 1 単語または 2 単語程度で抽出
- タイムアウト: 60 秒
- 失敗時は警告ログ + `None` 返却

### embed_frontmatter_fields ノード

```python
def embed_frontmatter_fields(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, str]:
    """Embed genre, topic, summary into frontmatter content.

    No file I/O - replaces move_to_vault.
    Returns dict[filename, markdown_content]
    """
```

**処理フロー:**
1. `genre`, `topic` をアイテムから取得
2. `summary` を `metadata` または `generated_metadata` から取得
3. frontmatter をパース
4. `summary`, `genre`, `topic` フィールドを追加
5. 更新された Markdown を返却（**ファイル I/O なし**）

**戻り値:**
- `dict[str, str]`: `{filename_without_extension: markdown_content}`
- `organized_notes` PartitionedDataset (TextDataset) に保存

### パイプライン変更

**変更前:**
```
classify_genre → normalize_frontmatter → clean_content → determine_vault_path → move_to_vault
```

**変更後:**
```
classify_genre → extract_topic → normalize_frontmatter → clean_content → embed_frontmatter_fields
```

**削除されたノード:**
- `determine_vault_path`: genre → vault_path マッピング（不要に）
- `move_to_vault`: ファイルシステム書き込み（廃止）

**追加されたノード:**
- `extract_topic`: LLM で topic 抽出
- `embed_frontmatter_fields`: genre, topic, summary を frontmatter に埋め込み

## Vault 書き込み検証

```
$ ls -la Vaults/
ls: cannot access 'Vaults/': No such file or directory
```

**確認内容:**
- `Vaults/` ディレクトリが存在しない → ファイル書き込みが発生していない
- `embed_frontmatter_fields` はメモリ上で処理し、PartitionedDataset に保存
- 最終出力: `data/07_model_output/organized/*.md`

## 注意点・次 Phase への引き継ぎ

### 統合テスト更新

- `tests/test_integration.py` および `tests/test_pipeline_registry.py` の期待ノード名を更新した
- 新しいパイプライン構造（extract_topic, embed_frontmatter_fields）を反映

### 既存機能の保持

- `determine_vault_path` および `move_to_vault` 関数は削除されていない（後方互換性のため Phase 6 で削除予定）
- パイプライン登録からのみ削除されている

### 次 Phase (Phase 3) への準備

- ゴールデンファイルの再生成が必要（現在は `format_markdown` 出力）
- `make test-e2e` および `make test-e2e-update-golden` の Makefile ターゲット更新が必要
- ゴールデンファイルに `genre`, `topic`, `summary` が含まれることを確認

### データセット構成

- `topic_extracted_items`: JSON (data/07_model_output/topic_extracted)
- `organized_notes`: Markdown (data/07_model_output/organized) ← **最終出力**

## ステータス

Phase 2: **Complete**

次 Phase: Phase 3 - User Story 1 (パイプライン最終出力のゴールデンファイル比較)
