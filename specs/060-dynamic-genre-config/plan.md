# Implementation Plan: ジャンル定義の動的設定

**Branch**: `060-dynamic-genre-config` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/060-dynamic-genre-config/spec.md`

## Summary

`genre_vault_mapping` の構造を拡張し、ジャンル定義（description）を含めることで、LLM プロンプトを動的に生成する。また、other 分類が5件以上の場合に新ジャンル候補を自動提案する機能を追加し、other 率を継続的に低減するサイクルを実現する。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, PyYAML 6.0+, requests (Ollama API)
**Storage**: ファイルシステム (YAML, Markdown, JSON)
**Testing**: unittest (標準ライブラリ)
**Target Platform**: Linux/macOS (ローカル実行)
**Project Type**: Single project (Kedro pipeline)
**Performance Goals**: パイプライン実行時間 ±10% 以内
**Constraints**: Ollama API 依存、other 分析は追加 LLM 呼び出し1回
**Scale/Scope**: 11ジャンル（拡張可能）、数百〜数千ファイル処理

## Constitution Check

*GATE: Constitution file not found - skipping formal gate check.*

既存プロジェクトパターンに準拠:
- [x] Kedro パイプライン構造を維持
- [x] 既存の nodes.py パターンに従う
- [x] パラメータは conf/ 配下で管理
- [x] テストは tests/ 配下に配置

## Project Structure

### Documentation (this feature)

```text
specs/060-dynamic-genre-config/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipelines/
│   └── organize/
│       ├── nodes.py     # 変更対象: プロンプト動的生成、other 分析
│       └── pipeline.py  # 変更対象: analyze_other_genres ノード追加
└── utils/
    └── ollama.py        # 既存: Ollama API ヘルパー

conf/
├── base/
│   └── parameters_organize.local.yml.example  # 変更対象: 新形式
└── local/
    └── parameters_organize.yml                # ユーザー設定（git-ignored）

data/07_model_output/
└── genre_suggestions.md  # 新規: other 分析結果

tests/
└── pipelines/
    └── organize/
        └── test_nodes.py  # 変更対象: 新テスト追加
```

**Structure Decision**: 既存の Kedro 単一プロジェクト構造を維持。新規ファイルは `genre_suggestions.md` のみ。

## Implementation Phases

### Phase 1: 設定形式の拡張

**目標**: `genre_vault_mapping` に description を追加

**変更ファイル**:
- `conf/base/parameters_organize.local.yml.example`
- `conf/local/parameters_organize.yml`

**新形式**:
```yaml
genre_vault_mapping:
  ai:
    vault: "エンジニア"
    description: "AI/機械学習/LLM/生成AI/Claude/ChatGPT"
  devops:
    vault: "エンジニア"
    description: "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS"
```

### Phase 2: プロンプト動的生成

**目標**: `genre_vault_mapping` からプロンプトを動的生成

**変更ファイル**:
- `src/obsidian_etl/pipelines/organize/nodes.py`

**実装**:
- `_build_genre_prompt(genre_definitions: dict) -> str` 関数追加
- `_extract_topic_and_genre_via_llm` でパラメータからジャンル定義を読み込み
- valid_genres を動的に構築

### Phase 3: other 分析・提案機能

**目標**: other が5件以上の場合に新ジャンル候補を提案

**変更ファイル**:
- `src/obsidian_etl/pipelines/organize/nodes.py`
- `src/obsidian_etl/pipelines/organize/pipeline.py`

**実装**:
- `analyze_other_genres(partitioned_input, params)` ノード追加
- LLM で other コンテンツを分析し、共通パターンを抽出
- `genre_suggestions.md` に提案を出力

### Phase 4: テスト・検証

**目標**: 既存テスト PASS + 新機能テスト追加

**変更ファイル**:
- `tests/pipelines/organize/test_nodes.py`

**テストケース**:
- 新形式の設定読み込み
- プロンプト動的生成
- other 分析トリガー条件
- 提案ファイル出力

## Complexity Tracking

| 項目 | 複雑度 | 理由 |
|------|--------|------|
| 設定形式変更 | 低 | YAML 構造の拡張のみ |
| プロンプト動的生成 | 低 | 文字列操作のみ |
| other 分析 | 中 | 追加 LLM 呼び出し |
| 後方互換性 | 低 | 旧形式は使用されていない（今回削除済み） |
