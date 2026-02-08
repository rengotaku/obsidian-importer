# Research: Kedro 入力フロー修正

## R-1: ZIP バイナリファイルの Kedro DataCatalog 経由読み込み

**Decision**: カスタム `BinaryDataset`（`AbstractDataset` サブクラス）を作成

**Rationale**:
- kedro-datasets に ZIP/raw bytes 読み込み用のデータセットが存在しない
- `PickleDataset`: pickle 形式（`pickle.load`）専用。raw bytes を返さない
- `TextDataset`: `open(mode="r")` で UTF-8 文字列を返す。バイナリ不可
- `AbstractDataset` は `load()`, `save()`, `_describe()` の3メソッド実装のみで十分
- `PartitionedDataset` の `dataset` パラメータに指定可能

**Alternatives considered**:
1. ノード内でファイルシステム直接読み込み → DataCatalog を迂回し、テスタビリティ低下
2. `parameters.yml` でディレクトリパス指定 → PartitionedDataset の自動パーティション検出を失う
3. `TextDataset` + base64 エンコード → 不必要な複雑さ

**Implementation**: ~30 行の軽量実装

```python
class BinaryDataset(AbstractDataset[bytes, bytes]):
    def __init__(self, *, filepath: str, metadata=None):
        self._filepath = filepath
    def load(self) -> bytes:
        with open(self._filepath, "rb") as f:
            return f.read()
    def save(self, data: bytes) -> None:
        with open(self._filepath, "wb") as f:
            f.write(data)
    def _describe(self) -> dict:
        return {"filepath": self._filepath}
```

## R-2: Kedro dispatch 型パイプライン設計パターン

**Decision**: `register_pipelines()` で `import.provider` パラメータに基づき `__default__` パイプラインを動的に構成する dispatch 型設計

**Rationale**:
- `kedro run` だけで動作する（`--pipeline` 指定不要）
- `parameters.yml` の `import.provider` で制御可能
- `kedro run --pipeline=import_claude` も引き続き使える（互換性維持）
- `register_pipelines()` は静的だが、`OmegaConf` で `parameters.yml` を直接読み込むことで provider を取得可能

**Alternatives considered**:
1. `before_pipeline_run` Hook で provider 判定 → パイプラインの差し替えが Kedro API で困難
2. 単一パイプライン内で条件分岐ノード → Kedro のノードは純粋関数であるべき
3. `KedroContext` のサブクラス → 過剰な抽象化
4. `__default__` 固定 + `--pipeline` で明示指定 → `kedro run` 単体で動かず UX が悪い

**Final approach**: `register_pipelines()` 内で `conf/base/parameters.yml` を読み込み、`import.provider` に基づいて `__default__` を動的に決定。個別パイプライン名（`import_claude`, `import_openai`, `import_github`）も互換性のため残す。無効な provider にはわかりやすいエラーメッセージ。

## R-3: Claude Extract ノードの ZIP 対応パターン

**Decision**: OpenAI の `parse_chatgpt_zip` と同じ `dict[str, Callable]` パターンに統一

**Rationale**:
- OpenAI ノードが既に以下のパターンで動作:
  1. `partitioned_input: dict[str, callable]` を受け取り
  2. 各パーティションの `load_func()` を呼び出して ZIP bytes を取得
  3. `_extract_conversations_from_zip(zip_bytes)` で `conversations.json` を抽出
- Claude も同じ ZIP 構造（直下に `conversations.json`）のため、同一パターンが適用可能
- 既存のパースロジック（`_validate_structure`, `_format_conversation_content`, チャンク分割）は変更不要

**Implementation changes**:
- `parse_claude_json(conversations: list[dict])` → `parse_claude_zip(partitioned_input: dict[str, callable])`
- ZIP 展開 → `conversations.json` 抽出ロジックを追加
- 抽出後は既存のループ処理をそのまま適用

## R-4: GitHub パイプラインのカタログ接続

**Decision**: カタログから `raw_github_posts` の入力定義を削除。中間データはメモリ渡し。

**Rationale**:
- `clone_github_repo` は URL → git clone → ファイルシステム → `dict[str, callable]` を返す
- これはカタログ管理のデータセットではなく、ノードが動的に生成するデータ
- Kedro ではカタログに定義されていないデータセットは `MemoryDataset` として自動処理される
- `raw_github_posts` と `parsed_github_items` をカタログから削除すれば、ノード出力がそのまま次ノードの入力になる

**Verification**: GitHub テスト用 URL `https://github.com/rengotaku/rengotaku.github.io/tree/master/test_posts`
