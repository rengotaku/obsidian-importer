# Data Model: Kedro 入力フロー修正

## Entities

### E-1: BinaryDataset

Kedro `AbstractDataset` のサブクラス。ZIP ファイルをバイナリとして読み書きする。

| Attribute | Type | Description |
|-----------|------|-------------|
| filepath | str | ファイルパス（Kedro が自動設定） |

**Operations**:
- `load() -> bytes`: ファイルをバイナリモードで読み込み
- `save(data: bytes) -> None`: バイナリデータをファイルに書き込み
- `_describe() -> dict`: データセットの説明（filepath）

**Usage**: `PartitionedDataset` の `dataset` パラメータに指定。`catalog.yml` で以下のように使用:

```yaml
raw_claude_conversations:
  type: partitions.PartitionedDataset
  path: data/01_raw/claude
  dataset:
    type: obsidian_etl.datasets.BinaryDataset
  filename_suffix: ".zip"
```

### E-2: DataCatalog エントリ（変更前後）

#### Claude (変更)

| 項目 | Before | After |
|------|--------|-------|
| type | PartitionedDataset | PartitionedDataset |
| path | data/01_raw/claude | data/01_raw/claude |
| dataset | json.JSONDataset | obsidian_etl.datasets.BinaryDataset |
| filename_suffix | .json | .zip |

#### OpenAI (変更)

| 項目 | Before | After |
|------|--------|-------|
| type | PartitionedDataset | PartitionedDataset |
| path | data/01_raw/openai | data/01_raw/openai |
| dataset | json.JSONDataset | obsidian_etl.datasets.BinaryDataset |
| filename_suffix | .json | .zip |

#### GitHub (変更)

| 項目 | Before | After |
|------|--------|-------|
| raw_github_posts | PartitionedDataset (catalog) | 削除（MemoryDataset 自動） |
| parsed_github_items | なし | 削除不要（MemoryDataset 自動） |

### E-3: ノードシグネチャ（変更前後）

#### parse_claude_json → parse_claude_zip

| 項目 | Before | After |
|------|--------|-------|
| 関数名 | parse_claude_json | parse_claude_zip |
| 入力 | conversations: list[dict] | partitioned_input: dict[str, Callable] |
| 出力 | dict[str, dict] | dict[str, dict]（変更なし） |

内部フロー（After）:
1. `partitioned_input` をイテレート
2. 各パーティションの `load_func()` で ZIP bytes を取得
3. ZIP から `conversations.json` を抽出して `list[dict]` を得る
4. 既存のパースロジック（フィルタ、チャンク分割等）を適用

#### parse_chatgpt_zip（変更なし）

既に `dict[str, Callable]` を受け取る設計。カタログ修正のみ。

#### clone_github_repo（変更なし）

ノード自体は変更不要。カタログ接続の修正のみ。

### E-4: パラメータ（変更前後）

```yaml
# Before
import:
  provider: claude

# After
import:
  provider: claude  # claude | openai | github

github_url: ""  # GitHub URL (import_github パイプライン用)
github_clone_dir: ""  # 一時クローンディレクトリ（空ならシステムtemp使用）
```

## State Transitions

本フィーチャーに状態遷移はない。データは Extract → Transform → Organize の一方向フロー。
