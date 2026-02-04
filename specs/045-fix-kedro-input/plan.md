# Implementation Plan: Kedro 入力フロー修正

**Branch**: `045-fix-kedro-input` | **Date**: 2026-02-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/045-fix-kedro-input/spec.md`

## Summary

`kedro run` が動作しない原因は、DataCatalog 定義とノードの入力シグネチャの型不一致。3プロバイダー（Claude, OpenAI, GitHub）それぞれで異なる問題がある。Claude/OpenAI は ZIP 入力に統一し、GitHub は URL パラメータ維持。パイプラインは dispatch 型設計に変更し、`import.provider` で振り分ける。

## Technical Context

**Language/Version**: Python 3.13 + Kedro 1.1.1
**Primary Dependencies**: kedro 1.1.1, kedro-datasets (PartitionedDataset, json, text), tenacity 8.x
**Storage**: ファイルシステム（JSON, JSONL, Markdown, ZIP）、Kedro DataCatalog
**Testing**: unittest（標準ライブラリ）、178 既存テスト
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（Kedro パイプラインプロジェクト）
**Performance Goals**: N/A（バッチ処理、リアルタイム性不要）
**Constraints**: Ollama ローカルサーバー依存（Transform フェーズ）
**Scale/Scope**: 数百〜数千会話の一括処理

## Constitution Check

*GATE: No constitution file found. Proceeding without gate checks.*

## Project Structure

### Documentation (this feature)

```text
specs/045-fix-kedro-input/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (catalog.yml contract)
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipeline_registry.py     # [変更] dispatch 型に書き換え
├── hooks.py                 # [変更なし]
├── datasets/                # [新規] カスタムデータセット
│   ├── __init__.py
│   └── binary_dataset.py    # BinaryDataset（ZIP バイナリ読み込み用）
└── pipelines/
    ├── extract_claude/
    │   ├── nodes.py          # [変更] list[dict] → dict[str, Callable] (ZIP bytes)
    │   └── pipeline.py       # [変更] 入力データセット名変更
    ├── extract_openai/
    │   ├── nodes.py          # [変更なし] 既に dict[str, Callable] 対応
    │   └── pipeline.py       # [変更なし]
    ├── extract_github/
    │   ├── nodes.py          # [変更なし]
    │   └── pipeline.py       # [変更] カタログ接続修正
    ├── transform/             # [変更なし]
    └── organize/              # [変更なし]

conf/base/
├── catalog.yml               # [変更] Claude/OpenAI: BinaryDataset、GitHub: カタログ定義削除
└── parameters.yml            # [変更] import.provider 維持、github_url / github_clone_dir 追加

tests/
├── fixtures/
│   ├── claude_test.zip        # [新規] 作成済み
│   ├── openai_test.zip        # [新規] 作成済み
│   ├── claude_input.json      # [既存] 互換性のため残す
│   └── github_jekyll_post.md  # [既存]
├── pipelines/
│   ├── extract_claude/
│   │   └── test_nodes.py      # [変更] ZIP 入力テストに更新
│   └── extract_openai/
│       └── test_nodes.py      # [変更] カタログ型テスト追加
├── test_integration.py        # [変更] ZIP 入力対応、dispatch テスト追加
├── test_pipeline_registry.py  # [変更] dispatch 型テスト
└── test_datasets.py           # [新規] BinaryDataset テスト
```

**Structure Decision**: 既存の Kedro プロジェクト構造を維持。`src/obsidian_etl/datasets/` に カスタムデータセットを追加するのみ。

## Design Decisions

### D-1: ZIP バイナリ読み込み方式

**問題**: kedro-datasets に ZIP/バイナリファイルを読み込むデータセットがない。

**選択**: カスタム `BinaryDataset`（`AbstractDataset` サブクラス）を作成。

**理由**:
- `PickleDataset` は pickle 形式専用で raw bytes 読み込みに非対応
- `TextDataset` は UTF-8 文字列を返すため ZIP バイナリに非対応
- `AbstractDataset` は `load`, `save`, `_describe` の3メソッド実装のみで軽量

**却下案**:
- ノード内で直接ファイル読み込み → Kedro の DataCatalog 設計思想に反する
- `parameters.yml` でパス指定 → PartitionedDataset の恩恵（複数ファイル自動検出）を失う

### D-2: dispatch 型パイプライン設計

**問題**: 現状は `import_claude`, `import_openai`, `import_github` の3パイプラインが個別登録。

**選択**: `register_pipelines()` で `import.provider` パラメータに基づき `__default__` パイプラインを動的に構成。個別パイプライン名も互換性のため残す。

**理由**:
- `kedro run` だけで動作する（`--pipeline` 指定不要）
- `parameters.yml` の `import.provider` で制御可能
- `kedro run --pipeline=import_claude` も引き続き使える

### D-3: Claude Extract ノードの ZIP 対応

**問題**: `parse_claude_json` は `conversations: list[dict]` を期待。ZIP 入力に変更が必要。

**選択**: OpenAI と同じパターン（`dict[str, Callable]` → `load_func()` → ZIP bytes → JSON 抽出）に統一。

**理由**:
- OpenAI の `parse_chatgpt_zip` が既にこのパターンで動作
- 両プロバイダーの入力処理が統一され保守性が向上
- 既存のパースロジック（メッセージフィルタ、チャンク分割等）はそのまま再利用

### D-4: GitHub パイプラインのカタログ接続

**問題**: `clone_github_repo` は URL string を入力、`dict[str, callable]` を出力するが、カタログで `raw_github_posts` が PartitionedDataset として定義されており接続が壊れている。

**選択**: カタログから `raw_github_posts` の入力定義を削除。`clone_github_repo` はパラメータから URL を受け取り、出力はメモリ上の `dict[str, callable]` として次ノードに直接渡す。中間データセット `parsed_github_items` もメモリデータセットとする。

**理由**:
- GitHub は URL → git clone → ファイル読み込みという特殊フローのため、ファイルベースのカタログ定義が不適
- ノード間のデータ受け渡しはメモリで十分（データ量が小さい）
- ノードのビジネスロジック変更が不要

## Phases

### Phase 1: BinaryDataset + Claude ZIP 対応 (Setup + TDD)

**目標**: カスタム BinaryDataset を作成し、Claude パイプラインが ZIP 入力で動作するようにする。

**変更ファイル**:
- `src/obsidian_etl/datasets/__init__.py` [新規]
- `src/obsidian_etl/datasets/binary_dataset.py` [新規]
- `src/obsidian_etl/pipelines/extract_claude/nodes.py` [変更]
- `src/obsidian_etl/pipelines/extract_claude/pipeline.py` [変更]
- `conf/base/catalog.yml` [変更]
- `tests/test_datasets.py` [新規]
- `tests/pipelines/extract_claude/test_nodes.py` [変更]

**検証**: `make test` パス + Claude Extract ノードが ZIP からパースできること

**アウトプット検証（parsed_items）**:
- `claude_test.zip` → 3 件の parsed_items が生成されること
- 各 parsed_item に必須フィールドが存在: `item_id`, `source_provider`, `content`, `file_id`, `messages`, `conversation_name`, `created_at`
- `source_provider` が `"claude"` であること
- `messages` の件数が元データと一致（各4メッセージ）
- `content` が空でないこと
- `is_chunked` が `False`（全会話が25000文字未満のため）

### Phase 2: OpenAI カタログ修正

**目標**: OpenAI パイプラインのカタログ定義を BinaryDataset に変更し、ノードとの型整合を確保する。

**変更ファイル**:
- `conf/base/catalog.yml` [変更]
- `tests/pipelines/extract_openai/test_nodes.py` [変更]

**検証**: `make test` パス + OpenAI Extract ノードが ZIP からパースできること

**アウトプット検証（parsed_items）**:
- `openai_test.zip` → 3 件の parsed_items が生成されること（メッセージ数が MIN_MESSAGES 以上の会話のみ）
- 各 parsed_item に必須フィールドが存在: `item_id`, `source_provider`, `content`, `file_id`, `messages`, `conversation_name`, `created_at`
- `source_provider` が `"openai"` であること
- `content` が空でないこと

### Phase 3: GitHub カタログ接続修正

**目標**: GitHub パイプラインのカタログ定義とノード接続を修正する。

**変更ファイル**:
- `conf/base/catalog.yml` [変更]
- `conf/base/parameters.yml` [変更]
- `src/obsidian_etl/pipelines/extract_github/pipeline.py` [変更]
- `tests/pipelines/extract_github/test_nodes.py` [変更]

**検証**: `make test` パス

### Phase 4: dispatch 型パイプライン + 統合テスト

**目標**: `pipeline_registry.py` を dispatch 型に変更し、統合テストを ZIP 入力対応に更新する。

**変更ファイル**:
- `src/obsidian_etl/pipeline_registry.py` [変更]
- `tests/test_pipeline_registry.py` [変更]
- `tests/test_integration.py` [変更]

**検証**: `make test` 全パス + dispatch 動作確認

### Phase 5: Polish

**目標**: ドキュメント更新、不要コード削除、最終検証。

**変更ファイル**:
- `CLAUDE.md` [変更]
- `conf/base/parameters.yml` [変更]

**検証**: `make test` 全パス、`make lint` パス

## Complexity Tracking

本修正は入力層の整合性修正が主であり、複雑な新規アーキテクチャの導入はない。カスタムデータセット（BinaryDataset）は ~30 行の軽量実装。
