# Research: データパイプラインの構造的再設計（Kedro 移行）

**Date**: 2026-02-04
**Spec**: [spec.md](spec.md)

## Research Topics

### R-1: Kedro バージョンと Python 互換性

**Decision**: Kedro 1.1.1（2025-11 リリース）を採用

**Rationale**:
- Python 3.10-3.13 対応。本プロジェクトの Python 3.11+ 要件を完全サポート
- Kedro 0.19 系は EOL（0.19.15 が最終）。1.0+ は破壊的変更あり → 新規移行なら最新を選択
- `KedroDataCatalog` → `DataCatalog` へリネーム済み（1.0 の変更）

**Alternatives considered**:
- Kedro 0.19.15: EOL のため不採用
- Prefect / Airflow: 分散実行向け。単一ユーザー・ローカル実行には過剰
- Luigi: メンテナンス頻度低下。Kedro の方がエコシステムが活発

---

### R-2: PartitionedDataset と冪等性パターン

**Decision**: PartitionedDataset + ノード内冪等チェック

**Rationale**:
- `PartitionedDataset` は `Dict[str, Callable]`（partition_id → lazy load）を返す
- `IncrementalDataset`（チェックポイント付き）も検討したが、アイテム単位の冪等性にはノード内スキップロジックの方が柔軟
- `overwrite=False`（デフォルト）で既存パーティションを保持
- ノード関数内で出力パーティションの存在チェック → 存在すればスキップ

**Alternatives considered**:
- `IncrementalDataset` のみ: チェックポイントは「最後に処理した位置」の概念。個別アイテムの成功/失敗は追跡できない
- カスタム Dataset: 実装コスト高。PartitionedDataset で十分

**Gotchas**:
- Kedro はパーティション単位の DAG 展開をサポートしない。全アイテムが 1 ノードに渡される
- → 「全アイテム Extract」→「全アイテム Transform」→「全アイテム Load」のバッチ処理パターン
- メモリ: lazy load 関数の参照のみ保持。数千ファイルでも問題なし

---

### R-3: ノード設計パターン（バッチ vs ストリーミング）

**Decision**: バッチ処理（全アイテムを 1 ノードで処理）+ ノード内イテレーション

**Rationale**:
- Kedro の PartitionedDataset は全パーティションを 1 ノードに渡す設計
- 現行の「アイテム単位で E→T→L を通す」パターンは Kedro では不可能（fan-out 未サポート）
- ノード関数内で `for item_id, load_fn in partitions.items():` でイテレーション
- 各アイテムの処理結果を `Dict[str, Any]` として返却 → 次のノードの PartitionedDataset 入力に

**Impact**:
- 現行: 1アイテムが E→T→L を逐次通過（ストリーミング）
- 新: 全アイテム E → 全アイテム T → 全アイテム L（バッチ）
- LLM 呼び出し（Transform）がボトルネック。バッチでも逐次でも総処理時間は同等
- メリット: 中間データが全て永続化される → デバッグ・部分再実行が容易

---

### R-4: マルチプロバイダーのパイプライン構成

**Decision**: プロバイダー別の名前付きパイプライン + 共通 Transform/Load パイプライン

**Rationale**:
- Kedro に条件分岐ノードのネイティブサポートなし
- プロバイダー別に Extract パイプラインを分離し、Transform/Load を共有するのが自然
- `pipeline_registry.py` で `import_claude`, `import_openai`, `import_github` を登録
- `kedro run --pipeline=import_claude` で実行

```python
def register_pipelines():
    extract_claude = create_claude_extract_pipeline()
    extract_openai = create_openai_extract_pipeline()
    extract_github = create_github_extract_pipeline()
    transform = create_transform_pipeline()
    organize = create_organize_pipeline()

    return {
        "import_claude": extract_claude + transform + organize,
        "import_openai": extract_openai + transform + organize,
        "import_github": extract_github + transform + organize,
        "__default__": extract_claude + transform + organize,
    }
```

**Alternatives considered**:
- 単一 extract ノード + ディスパッチャー関数: spec の clarification で決定されたが、Kedro の設計思想に合わない。パイプライン分離の方が DAG が明確
- タグベース実行: `kedro run --tags=claude` でも可能だが、パイプライン名の方が意図が明確

**Spec との差異**:
- spec v1.2 は「単一 extract ノード + ディスパッチャー」を明記しているが、Kedro の制約上、プロバイダー別パイプラインの方が適切
- ディスパッチャーパターンはノード内部で実現可能だが、DAG の可読性が低下する
- → **spec の意図（Dataset 定義の統一）は維持しつつ、パイプライン分離で実現する**

---

### R-5: エラーハンドリング戦略

**Decision**: ノード内 try/except（アイテム単位）+ on_node_error Hook（ノード単位ログ）

**Rationale**:
- `on_node_error` は「ノードが例外を投げた時」に発火。しかしノード内でアイテム単位エラーを処理する場合、ノード自体は例外を投げない
- → アイテム単位のエラーはノード関数内で `try/except` し、失敗アイテムを `Dict` に記録して返却
- ノード全体の予期しないクラッシュは `on_node_error` Hook でキャッチ

```python
def transform_items(partitions: Dict[str, Callable], params: dict) -> Dict[str, dict]:
    results = {}
    for item_id, load_fn in partitions.items():
        try:
            data = load_fn()
            results[item_id] = process(data, params)
        except Exception as e:
            logger.error(f"Failed: {item_id}: {e}")
            # 失敗アイテムは出力に含めない → 再実行時に再処理
    return results
```

**Alternatives considered**:
- `before_node_run` Hook でリトライラップ: ノード全体のリトライであり、アイテム単位ではない
- カスタム Runner: 過剰な複雑さ

---

### R-6: tenacity リトライの統合

**Decision**: ノード関数内で tenacity デコレータを直接使用

**Rationale**:
- LLM 呼び出しノード（extract_knowledge）で Ollama API のリトライが必要
- ノード関数内のヘルパー関数に `@retry` デコレータを適用
- Hook ベースのリトライはノード全体に適用されるため、アイテム単位リトライには不向き

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_ollama(prompt: str, params: dict) -> dict:
    # Ollama API call
    ...

def extract_knowledge(partitions: Dict, params: dict) -> Dict:
    for item_id, load_fn in partitions.items():
        result = call_ollama(prompt, params)  # retries automatically
```

---

### R-7: Kedro プロジェクト初期化とディレクトリ構成

**Decision**: `kedro new` でスケルトン生成 → 既存ロジック移植

**Rationale**:
- spec clarification で「`kedro new` を実際に実行」と決定済み
- `kedro new --name=obsidian-etl --tools=lint,test --example=n`
- 生成後、既存の `src/etl/` のロジックを新構造に移植

**Target Structure**:
```
src/obsidian_etl/           # kedro new が生成するパッケージ
├── __init__.py
├── settings.py             # Hook 登録、セッション設定
├── pipeline_registry.py    # パイプライン登録
├── pipelines/
│   ├── extract_claude/     # Claude Extract パイプライン
│   │   ├── __init__.py
│   │   ├── nodes.py        # parse_claude_json, validate_structure, validate_content
│   │   └── pipeline.py     # pipeline 定義
│   ├── extract_openai/     # ChatGPT Extract パイプライン
│   │   ├── __init__.py
│   │   ├── nodes.py        # parse_chatgpt_zip, validate_min_messages
│   │   └── pipeline.py
│   ├── extract_github/     # GitHub Extract パイプライン
│   │   ├── __init__.py
│   │   ├── nodes.py        # clone_repo, parse_jekyll, convert_frontmatter
│   │   └── pipeline.py
│   ├── transform/          # 共通 Transform パイプライン
│   │   ├── __init__.py
│   │   ├── nodes.py        # extract_knowledge, generate_metadata, format_markdown
│   │   └── pipeline.py
│   └── organize/           # Organize パイプライン（Extract + Transform + Load）
│       ├── __init__.py
│       ├── nodes.py        # read_markdown, classify_genre, normalize, clean, move_to_vault
│       └── pipeline.py
├── hooks.py                # ErrorHandlerHook, LoggingHook
├── datasets/               # カスタム Dataset（必要に応じて）
│   └── __init__.py
└── utils/                  # ユーティリティ（リファクタ移植）
    ├── ollama.py           # Ollama API クライアント
    ├── knowledge_extractor.py  # LLM 知識抽出
    ├── chunker.py          # チャンク分割
    ├── file_id.py          # SHA256 file_id
    └── prompts/            # LLM プロンプトテンプレート
conf/
├── base/
│   ├── catalog.yml         # データセット定義
│   └── parameters.yml      # パイプラインパラメータ
└── local/
    └── catalog.yml         # ローカルパス上書き
tests/
├── pipelines/
│   ├── extract_claude/
│   │   └── test_nodes.py
│   ├── extract_openai/
│   │   └── test_nodes.py
│   ├── extract_github/
│   │   └── test_nodes.py
│   ├── transform/
│   │   └── test_nodes.py
│   └── organize/
│       └── test_nodes.py
├── test_hooks.py
└── conftest.py             # 共通フィクスチャ
```

---

### R-8: テスト戦略

**Decision**: unittest ベースのノード単体テスト + Kedro Runner 統合テスト

**Rationale**:
- spec で「TDD（RED→GREEN）はノードのみ。インフラ層は実装後テスト」と決定済み
- Kedro のノードは純粋関数 → `unittest.TestCase` で直接呼び出し可能
- ゴールデンデータ: 既存パイプラインの入出力を保存し、ノード単位で部分一致検証
- 統合テスト: `SequentialRunner` + テスト用 `DataCatalog` でパイプライン全体をテスト

**Testing Framework**: 引き続き `unittest`（spec 準拠）

---

### R-9: 旧 src/etl/ との並行運用と削除

**Decision**: 移行完了まで旧コードを残し、完了後に削除

**Rationale**:
- spec で「一括移行、旧コードとの互換性は維持しない」と決定済み
- 旧 `src/etl/` と新 `src/obsidian_etl/` は独立したパッケージ名 → 共存可能
- ゴールデンデータ生成のため、移行中は旧パイプラインを参照用に残す
- 全ノード TDD 完了 + 統合テスト PASS 後に `src/etl/` を削除

---

### R-10: データレイヤー設計（Kedro Data Engineering Convention）

**Decision**: Kedro 標準データレイヤーに準拠

**Rationale**:
- Kedro は `data/` ディレクトリを番号付きレイヤーで管理する慣例がある
- 本プロジェクトでは以下のマッピング:

| Layer | Path | 用途 |
|-------|------|------|
| 01_raw | `data/01_raw/` | プロバイダーからの入力（JSON, ZIP, git clone 結果） |
| 02_intermediate | `data/02_intermediate/` | Extract 出力（パース済みアイテム） |
| 03_primary | `data/03_primary/` | Transform 出力（LLM 処理済みアイテム） |
| 04_feature | `data/04_feature/` | Organize Extract 出力（Markdown 読み込み済み） |
| 05_model_input | — | 未使用 |
| 06_models | — | 未使用 |
| 07_model_output | `data/07_model_output/` | 最終 Markdown ファイル（Load 出力） |
| 08_reporting | — | 未使用 |

- 現行の `.staging/@session/` 構造は廃止。`data/` レイヤーに統合

**Alternative**: 現行の `.staging/` 構造を維持 → Kedro のカタログ設計思想に反するため不採用
