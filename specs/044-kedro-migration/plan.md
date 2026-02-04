# Implementation Plan: データパイプラインの構造的再設計（Kedro 移行）

**Branch**: `044-kedro-migration` | **Date**: 2026-02-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/044-kedro-migration/spec.md`

## Summary

現在の独自 ETL パイプライン（`src/etl/`、30,411 行、28 処理ステップ）を Kedro 1.1.1 に移行する。Phase/Stage/Step の独自階層を廃止し、Kedro の Pipeline/Node/DataCatalog に置き換える。プロバイダー別の名前付きパイプライン（Claude, OpenAI, GitHub）+ 共通 Transform + Organize パイプラインで DAG を構成し、PartitionedDataset + ノード内冪等チェックで Resume を実現する。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, tenacity 8.x, PyYAML 6.0+, requests 2.28+
**Storage**: ファイルシステム（JSON, JSONL, Markdown）、Kedro DataCatalog（PartitionedDataset）
**Testing**: unittest（標準ライブラリ）、ノード単体テスト + SequentialRunner 統合テスト
**Target Platform**: Linux（ローカル実行、単一ユーザー）
**Project Type**: Single（CLI パイプライン）
**Performance Goals**: 移行前の処理時間の 120% 以内（spec 成功基準）
**Constraints**: Ollama ローカル API（http://localhost:11434）、LLM 呼び出しがボトルネック
**Scale/Scope**: 数百〜数千の会話ファイル、3 プロバイダー（Claude, OpenAI, GitHub Jekyll）

## Constitution Check

*GATE: No constitution file found. Proceeding without constitution gates.*

Constitution ファイル（`.specify/memory/constitution.md`）が存在しないため、ゲートチェックは省略。プロジェクトの既存パターン（CLAUDE.md）に準拠する:

- [x] Python 標準ライブラリ中心の設計
- [x] unittest フレームワーク使用
- [x] Makefile ベースのビルド・テスト
- [x] レガシーコード（`src/converter/`）への非干渉
- [x] `src/rag/` への非影響

## Project Structure

### Documentation (this feature)

```text
specs/044-kedro-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── catalog.yml      # DataCatalog 定義
    └── parameters.yml   # パイプラインパラメータ
```

### Source Code (repository root)

```text
src/obsidian_etl/                    # Kedro パッケージ（kedro new で生成）
├── __init__.py
├── settings.py                      # Hook 登録、セッション設定
├── pipeline_registry.py             # パイプライン登録（全プロバイダー）
├── pipelines/
│   ├── extract_claude/              # Claude Extract
│   │   ├── __init__.py
│   │   ├── nodes.py                 # parse_claude_json, validate_structure, validate_content
│   │   └── pipeline.py
│   ├── extract_openai/              # ChatGPT Extract
│   │   ├── __init__.py
│   │   ├── nodes.py                 # parse_chatgpt_zip, validate_min_messages
│   │   └── pipeline.py
│   ├── extract_github/              # GitHub Jekyll Extract
│   │   ├── __init__.py
│   │   ├── nodes.py                 # clone_repo, parse_jekyll, convert_frontmatter
│   │   └── pipeline.py
│   ├── transform/                   # 共通 Transform（全プロバイダー共有）
│   │   ├── __init__.py
│   │   ├── nodes.py                 # extract_knowledge, generate_metadata, format_markdown
│   │   └── pipeline.py
│   └── organize/                    # Organize（ジャンル判定 + Vault 配置）
│       ├── __init__.py
│       ├── nodes.py                 # classify_genre, normalize_frontmatter, clean_content, move_to_vault
│       └── pipeline.py
├── hooks.py                         # ErrorHandlerHook, LoggingHook
└── utils/                           # ユーティリティ（既存からリファクタ移植）
    ├── __init__.py
    ├── ollama.py                    # Ollama API クライアント
    ├── knowledge_extractor.py       # LLM 知識抽出ロジック
    ├── chunker.py                   # チャンク分割
    ├── file_id.py                   # SHA256 file_id 生成
    └── prompts/                     # LLM プロンプトテンプレート
        ├── knowledge_extraction.txt
        └── summary_translation.txt

conf/
├── base/
│   ├── catalog.yml                  # DataCatalog 定義（全データセット）
│   ├── parameters.yml               # パイプラインパラメータ
│   └── logging.yml                  # ログ設定
└── local/
    └── catalog.yml                  # ローカルパス上書き

data/                                # Kedro データレイヤー
├── 01_raw/                          # 入力データ（プロバイダー固有形式）
├── 02_intermediate/                 # Extract 出力（パース済みアイテム）
├── 03_primary/                      # Transform 出力（LLM 処理済み）
└── 07_model_output/                 # 最終 Markdown（Vault 配置前）

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
└── fixtures/                        # ゴールデンデータ
    ├── claude_input.json
    ├── openai_input.zip
    └── expected_outputs/
```

**Structure Decision**: Kedro 標準の `src/<package>/pipelines/` 構造を採用。プロバイダー別に Extract パイプラインを分離し、Transform と Organize を共通パイプラインとして共有。`conf/` でデータセットとパラメータを宣言的に管理。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 5 パイプラインモジュール | 3 プロバイダー × Extract + 共通 Transform + Organize | 単一パイプライン + ディスパッチャーは DAG 可読性が低下 |
| utils/ の存在 | LLM 呼び出し・チャンク分割は複数パイプラインで共有 | 各パイプラインに重複コードを置くのは保守コスト増 |
