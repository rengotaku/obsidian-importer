# Phase 1 Output: Setup

**Date**: 2026-03-03
**Status**: Completed

## Executed Tasks

- [x] T001 Read: `conf/base/catalog.yml` の現在のデータセット定義を確認
- [x] T002 Read: `src/obsidian_etl/utils/log_context.py` の `iter_with_file_id` 実装を確認
- [x] T003 Read: `tests/` 配下の関連テストファイルを確認
- [x] T004 Read: `data/07_model_output/` の現在のディレクトリ構造を確認
- [x] T005 Edit: 本ファイルにセットアップ分析結果を記録

## Existing Code Analysis

### conf/base/catalog.yml

**Structure**:
- Layer 01 (raw): `raw_claude_conversations`, `raw_openai_conversations`
- Layer 02 (intermediate): `parsed_items`, `existing_parsed_items`
- Layer 03 (primary): `transformed_items_with_knowledge`, `transformed_items_with_metadata`
- Layer 07 (model_output): **JSON/MD 混在** ← 要修正

**JSON データセット（05_model_input へ移動対象）**:

| データセット名 | 現在のパス | 行番号 |
|---------------|-----------|--------|
| classified_items | data/07_model_output/classified | 122-131 |
| existing_classified_items | data/07_model_output/classified | 133-142 |
| topic_extracted_items | data/07_model_output/topic_extracted | 144-153 |
| normalized_items | data/07_model_output/normalized | 155-164 |
| cleaned_items | data/07_model_output/cleaned | 166-175 |
| vault_determined_items | data/07_model_output/vault_determined | 177-186 |
| organized_items | data/07_model_output/organized | 188-197 |

**MD データセット（07_model_output に維持）**:
- `markdown_notes` (100-109): data/07_model_output/notes
- `review_notes` (111-120): data/07_model_output/review
- `organized_notes` (199-208): data/07_model_output/organized
- `organized_files` (210-219): data/07_model_output/organized

**Required Updates**:
1. すべての JSON データセットの `path` を `data/05_model_input/` 配下に変更
2. `metadata.kedro-viz.layer` を `model_input` に変更

### src/obsidian_etl/utils/log_context.py

**Structure**:
- `_file_id_var: ContextVar[str]`: file_id のコンテキスト変数
- `set_file_id(file_id: str)`: file_id を設定
- `get_file_id() -> str`: file_id を取得
- `clear_file_id()`: file_id をクリア
- `_extract_file_id_from_frontmatter(content: str) -> str | None`: frontmatter から file_id 抽出
- `file_id_context(file_id: str)`: コンテキストマネージャー
- `iter_with_file_id(partitioned_input)`: **パーティションイテレータ（簡素化対象）**
- `ContextAwareFormatter`: ログフォーマッター
- `ContextAwareRichHandler`: Rich ハンドラー

**iter_with_file_id の現状（lines 130-175）**:

```python
def iter_with_file_id(
    partitioned_input: dict[str, callable] | list[tuple[str, callable]],
) -> Generator[tuple[str, any], None, None]:
    # Handle both dict and list of tuples
    items = partitioned_input.items() if isinstance(partitioned_input, dict) else partitioned_input

    for key, load_func in items:
        item = load_func()

        # Extract file_id from item, fallback to key
        file_id = key
        if isinstance(item, dict):           # ← dict 対応（削除対象）
            file_id = item.get("metadata", {}).get("file_id") or item.get("file_id") or key
        elif isinstance(item, str):          # ← str 対応（維持）
            extracted = _extract_file_id_from_frontmatter(item)
            if extracted:
                file_id = extracted

        with file_id_context(file_id):
            yield key, item
```

**Required Updates**:
1. `partitioned_input` の型を `dict[str, callable]` のみに変更
2. `if isinstance(item, dict):` ブロックを削除
3. `if isinstance(item, str):` を `str` 型チェックに変更し、非 str は TypeError
4. docstring を更新

### data/07_model_output/ ディレクトリ構造

**現在の状態**:
```
data/07_model_output/
├── classified/      # 492+ JSON files
├── cleaned/         # JSON files
├── normalized/      # 492 JSON files
├── organized/       # JSON + MD (混在)
├── notes/           # MD files
└── review/          # MD files
```

**注意点**:
- `topic_extracted/` と `vault_determined/` は現在存在しない（パイプライン実行時に作成）
- `organized/` には JSON と MD の両方が存在（特別な移行処理が必要）

## Existing Test Analysis

- `tests/utils/test_log_context.py`: iter_with_file_id の Markdown 処理テストが存在
  - `TestIterWithFileIdMarkdown`: str 入力のテスト (3 cases)
  - **dict 入力拒否のテストは存在しない** → Phase 4 で新規作成

**Does not exist**:
- `tests/unit/test_catalog_paths.py` → Phase 2 で新規作成
- `tests/unit/test_migrate_data_layers.py` → Phase 3 で新規作成

**Required Fixtures**:
- なし（各テストでモックを直接作成）

## Newly Created Files

なし（Phase 1 は分析のみ）

## Technical Decisions

1. **Layer 番号 05 を使用**: Kedro 公式慣例に従い、`05_model_input` は「モデルへの入力データ」を意味
2. **organized/ の分離**: JSON は `05_model_input/organized/`、MD は `07_model_output/organized/` に分離
3. **iter_with_file_id の簡素化**: データレイヤー分離後、dict 入力は不要になるため削除

## Handoff to Next Phase

### Phase 2 (US1 - catalog.yml 更新):

**実装対象**:
- `conf/base/catalog.yml` の 7 つの JSON データセットパスを `05_model_input/` に変更
- `data/05_model_input/` ディレクトリ構造を作成（.gitkeep 含む）

**再利用可能**:
- catalog.yml の既存構造とフォーマット
- PartitionedDataset 設定パターン

**注意点**:
- `metadata.kedro-viz.layer` も `model_input` に変更が必要
- テストは新パスを検証する単体テストを先に作成（TDD）

### Phase 3 (US2 - 移行スクリプト):

**実装対象**:
- `scripts/migrate_data_layers.py`: JSON ファイルを移行するスクリプト
- dry-run モード、サマリー出力、既存ファイルスキップ

**再利用可能**:
- `shutil.move` 標準ライブラリ
- `pathlib.Path` パターン

**注意点**:
- `organized/` は JSON のみ移行、MD は維持

### Phase 4 (US3 - iter_with_file_id 簡素化):

**実装対象**:
- `src/obsidian_etl/utils/log_context.py` の `iter_with_file_id` から dict 対応を削除
- str 型チェックと TypeError 追加

**再利用可能**:
- `_extract_file_id_from_frontmatter` 関数
- `file_id_context` コンテキストマネージャー

**注意点**:
- 既存の str 対応テストは維持
- dict 入力で TypeError をテストする新規テストが必要
