# Implementation Plan: Summary品質改善

**Branch**: `012-summary-quality` | **Date**: 2026-01-15 | **Spec**: [spec.md](spec.md)
**Input**: Claude会話ログのSummary品質改善 - 英語→日本語化、冗長な会話経緯説明→知識抽出型の簡潔な要約へ変換

## Summary

既存の`normalizer`パイプラインに新規Stage 5（Summary品質改善）を追加する。Stage 4（metadata生成）の後に実行し、Summaryセクションを「会話経緯説明」から「知識抽出型の構造化された要約」に変換する。

## Technical Context

**Language/Version**: Python 3.11+ (既存normalizer)
**Primary Dependencies**: 標準ライブラリ + Ollama API (既存)
**Storage**: ファイルシステム (Markdown)
**Testing**: pytest (既存テストスイート)
**Target Platform**: Linux (local)
**Project Type**: single (既存スクリプト拡張)
**Performance Goals**: 既存パイプラインと同等（API呼び出し1回追加）
**Constraints**: 既存パイプライン構造を維持しつつ新規Stage追加

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **II. Obsidian Markdown Compliance** | ✅ Pass | Summary形式はMarkdown準拠を維持 |
| **III. Normalization First** | ✅ Pass | 既存正規化フロー内で改善 |
| **V. Automation with Oversight** | ✅ Pass | 既存の確認フローを維持 |

**Constitution Violations**: なし

## Project Structure

### Documentation (this feature)

```text
specs/012-summary-quality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
├── prompts/
│   ├── stage1_dust.txt
│   ├── stage2_genre.txt
│   ├── stage3_normalize.txt
│   ├── stage4_metadata.txt
│   └── stage5_summary.txt        # 新規作成
├── normalizer/
│   ├── config.py                 # STAGE_PROMPTSに追加
│   ├── models.py                 # Stage5Result追加
│   └── pipeline/
│       ├── stages.py             # stage5_summary()追加
│       └── runner.py             # stage5呼び出し追加
└── ...
```

**Structure Decision**: 既存パイプライン構造を維持し、Stage 5として新規追加。

## Pipeline Flow (Updated)

```
pre_process → stage1_dust → stage2_genre → stage3_normalize → stage4_metadata → stage5_summary → post_process
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - 違反なし
