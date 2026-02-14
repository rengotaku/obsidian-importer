# Implementation Plan: Ollama パラメーター関数別設定

**Branch**: `051-ollama-params-config` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/051-ollama-params-config/spec.md`

## Summary

関数別パラメーター設定機能を実装する。`parameters.yml` の `ollama` セクションを `ollama.{関数名}` 形式に拡張し、`extract_knowledge`, `translate_summary`, `extract_topic` それぞれに異なるパラメーターを設定可能にする。また、`extract_topic` を `call_ollama` を使用する実装に統一する。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, PyYAML 6.0+, tenacity 8.x, requests 2.28+
**Storage**: ファイルシステム（YAML, JSON, JSONL, Markdown）、Kedro DataCatalog (PartitionedDataset)
**Testing**: unittest（Python標準ライブラリ）
**Target Platform**: Linux/macOS ローカル開発環境
**Project Type**: Single project (ETL pipeline)
**Performance Goals**: N/A（バッチ処理、LLM呼び出しがボトルネック）
**Constraints**: Ollama ローカルサーバー依存、既存パイプラインの後方互換性必須
**Scale/Scope**: 単一ユーザー向けローカルツール、会話数千件規模

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: `constitution.md` ファイルが存在しないため、プロジェクトの CLAUDE.md に記載された規約に基づいてチェックを行う。

| Gate | Status | Notes |
|------|--------|-------|
| 既存コード修正は `src/obsidian_etl/` のみ | ✅ PASS | レガシーコード (`src/converter/`) は修正しない |
| 後方互換性の維持 | ✅ PASS | デフォルト値により既存設定で動作 |
| テストは unittest 使用 | ✅ PASS | pytest 不使用 |
| Makefile ターゲット使用 | ✅ PASS | `make test` でテスト実行 |

## Project Structure

### Documentation (this feature)

```text
specs/051-ollama-params-config/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── parameters.yml   # 拡張後の parameters.yml 形式定義
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── utils/
│   ├── ollama.py              # call_ollama (変更なし)
│   ├── knowledge_extractor.py # extract_knowledge, translate_summary (パラメーター取得変更)
│   └── ollama_config.py       # [NEW] OllamaConfig ヘルパー
├── pipelines/
│   ├── transform/
│   │   └── nodes.py           # extract_knowledge ノード (パラメーター取得変更)
│   └── organize/
│       └── nodes.py           # extract_topic, _extract_topic_via_llm (call_ollama 使用に変更)

conf/base/
└── parameters.yml             # ollama セクション拡張

tests/
├── utils/
│   └── test_ollama_config.py  # [NEW] OllamaConfig テスト
└── pipelines/
    ├── transform/
    │   └── test_nodes.py      # パラメーター取得テスト追加
    └── organize/
        └── test_nodes.py      # extract_topic テスト追加
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規ファイルは `src/obsidian_etl/utils/ollama_config.py` のみ。

## Complexity Tracking

該当なし（Constitution Check に違反なし）

---

## Phase 0: Research Output

### Research Topics

1. **Kedro parameters.yml のネスト構造**
2. **既存 Ollama パラメーター取得パターン**
3. **extract_topic の現在の実装**

### Findings

#### 1. Kedro parameters.yml のネスト構造

**Decision**: `ollama.defaults` + `ollama.functions.{関数名}` の2層構造

**Rationale**:
- Kedro は YAML のネスト構造をそのまま dict として扱う
- 関数ごとのオーバーライドが可能になる
- デフォルト値を一箇所で管理できる

**Alternatives considered**:
- `ollama_extract_knowledge`, `ollama_translate_summary` のフラットキー → ネストの方が構造が明確
- `import.ollama.extract_knowledge` → `organize.ollama.extract_topic` と分離されてしまう

#### 2. 既存 Ollama パラメーター取得パターン

**Current State**:
- `extract_knowledge`: `params.get("ollama", {})` で全パラメーター取得
- `translate_summary`: 同上
- `extract_topic`: `params.get("ollama", {})` だが `requests.post` 直接呼び出し

**Decision**: 統一ヘルパー関数 `get_ollama_config(params, function_name)` を作成

**Rationale**:
- 各関数でのパラメーター取得ロジックを統一
- デフォルト値のフォールバック処理を一箇所に集約
- テスト容易性の向上

#### 3. extract_topic の現在の実装

**Current State** (`_extract_topic_via_llm`):
```python
response = requests.post(
    f"{base_url}/api/generate",
    json={"model": model, "prompt": prompt, "stream": False},
    timeout=60,
)
```

**Issues**:
- `/api/generate` エンドポイントを使用（chat API ではない）
- `call_ollama` と異なるエラーハンドリング
- パラメーター（temperature, num_predict）未対応

**Decision**: `call_ollama` を使用する実装に変更

**Rationale**:
- エラーハンドリングの統一
- パラメーター設定の一元化
- `num_predict` で出力トークン数を制限可能に

---

## Phase 1: Design & Contracts

### Data Model

→ [data-model.md](./data-model.md)

### API Contracts

→ [contracts/parameters.yml](./contracts/parameters.yml)

### Quickstart

→ [quickstart.md](./quickstart.md)
