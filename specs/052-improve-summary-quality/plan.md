# Implementation Plan: LLM まとめ品質の向上

**Branch**: `052-improve-summary-quality` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/052-improve-summary-quality/spec.md`

## Summary

LLM（Ollama）による会話履歴からの知識抽出において、過度な圧縮を防ぎ、重要情報を保持した高品質なまとめを生成する。プロンプト改善とゴールデンファイルによる品質検証を実装する。

## Technical Context

**Language/Version**: Python 3.11+ (Python 3.13 compatible)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, requests (Ollama API), PyYAML 6.0+
**Storage**: ファイルシステム (Markdown, JSON, JSONL)、Kedro PartitionedDataset
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux / macOS
**Project Type**: single (Kedro pipeline)
**Performance Goals**: 圧縮率しきい値達成率 80%以上、review フォルダ振り分け率 20%以下
**Constraints**: Ollama API タイムアウト 300秒以内
**Scale/Scope**: 10-12 件のゴールデンファイル、既存プロンプト改善

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| 単一プロジェクト構造 | ✅ PASS | 既存 Kedro パイプラインを拡張 |
| 後方互換性不要 | ✅ PASS | プロジェクト方針に従い破壊的変更可 |
| シンプルさ優先 | ✅ PASS | プロンプト改善 + ゴールデンファイル追加のみ |

## Project Structure

### Documentation (this feature)

```text
specs/052-improve-summary-quality/
├── spec.md              # 仕様書
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── checklists/          # チェックリスト
│   └── requirements.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── utils/
│   └── prompts/
│       └── knowledge_extraction.txt  # 改善対象プロンプト
├── pipelines/
│   └── transform/
│       └── nodes.py                  # extract_knowledge ノード
└── tests/

tests/
├── fixtures/
│   └── golden/                       # 新規: ゴールデンファイル (10-12件)
│       ├── README.md                 # ゴールデンファイル一覧
│       └── *.md                      # 各ゴールデンファイル
└── test_e2e_golden.py                # 新規: E2Eテスト
```

**Structure Decision**: 既存の Kedro パイプライン構造を維持。ゴールデンファイルは `tests/fixtures/golden/` に配置。

## Implementation Approach

### 1. プロンプト改善

現状の `knowledge_extraction.txt` に以下を追加/強化：

1. **理由・背景の説明指示**: 「なぜ」を含めた説明を要求
2. **表形式データの保持**: 表形式を検出したら必ず保持する指示
3. **数値・日付・固有名詞の保持**: 具体的な情報の省略禁止を強化
4. **分析・推奨の構造化**: 分析結果や推奨事項をセクション化

### 2. ゴールデンファイル選定

| 会話タイプ | 小 (<2KB) | 中 (2-5KB) | 大 (>5KB) | ソース |
|-----------|-----------|------------|-----------|--------|
| 技術系 | 1 件 | 1 件 | 1 件 | organized + review |
| ビジネス系 | 1 件 | 1 件 | - | organized |
| 日常系 | 1 件 | - | - | organized |
| 表形式データ含む | - | 1 件 | 1 件 | review |
| コード含む | 1 件 | 1 件 | - | organized + review |

**ソースディレクトリ**:
- `data/07_model_output/organized/` - 成功例
- `data/07_model_output/review/` - 改善対象

### 3. E2E テスト実装

```python
# tests/test_e2e_golden.py
def test_golden_files_meet_compression_threshold():
    """ゴールデンファイルが圧縮率しきい値を満たすことを検証"""

def test_golden_files_preserve_table_structure():
    """表形式データを含むファイルで表形式が保持されることを検証"""
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
