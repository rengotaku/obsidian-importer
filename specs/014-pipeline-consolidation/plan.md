# Implementation Plan: Normalizer Pipeline統合

**Branch**: `014-pipeline-consolidation` | **Date**: 2026-01-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-pipeline-consolidation/spec.md`

## Summary

既存の5段階LLMパイプラインを3段階に統合し、処理効率を改善する。
- Stage A: Dust判定 + ジャンル分類（Stage 1+2統合）
- Stage B: Markdown正規化（Stage 3維持）
- Stage C: メタデータ生成（Stage 4+5統合、summary/related追加）

## Technical Context

**Language/Version**: Python 3.11+ (標準ライブラリ中心)
**Primary Dependencies**: urllib, json, pathlib, re（標準ライブラリのみ）
**Storage**: Markdown files, JSON state files
**Testing**: pytest（既存 normalizer/tests/ 流用）
**Target Platform**: Linux/macOS CLI
**Project Type**: Single（既存normalizerパッケージ拡張）
**Performance Goals**: N/A（処理時間短縮はスコープ外）
**Constraints**: Ollama API (gpt-oss:20b), num_ctx: 16384
**Scale/Scope**: @index/配下のMarkdownファイル（数十〜数百件/セッション）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | frontmatter出力形式はspec準拠 |
| III. Normalization First | ✅ Pass | 正規化パイプラインの改善 |
| IV. Genre-Based Organization | ✅ Pass | Stage Aでジャンル分類維持 |
| V. Automation with Oversight | ✅ Pass | `unknown`→@review配置で人間確認 |

**Gate Result**: PASS - 違反なし

## Project Structure

### Documentation (this feature)

```text
specs/014-pipeline-consolidation/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
├── normalizer/
│   ├── models.py           # StageAResult, StageCResult追加
│   ├── pipeline/
│   │   ├── stages.py       # stage_a(), stage_c()追加、旧stage削除
│   │   ├── runner.py       # 新パイプライン実行ロジック
│   │   └── prompts.py      # プロンプト読み込み
│   ├── io/
│   │   └── ollama.py       # num_ctx設定追加
│   └── tests/
│       ├── test_pipeline.py    # Stage A/B/C テスト
│       └── test_validators.py  # 既存テスト維持
├── prompts/
│   ├── stage_a_classify.txt    # 新規: Dust+ジャンル統合プロンプト
│   └── stage_c_metadata.txt    # 新規: メタデータ+Summary統合プロンプト
└── ...
```

**Structure Decision**: 既存`normalizer/`パッケージ内で修正。新規ファイルはプロンプト2件のみ。

## Complexity Tracking

> **Gate violations**: None - 追加複雑性なし
