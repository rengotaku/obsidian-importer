# Implementation Plan: Robust JSON Parsing for LLM Responses

**Branch**: `005-robust-json-parse` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-robust-json-parse/spec.md`

## Summary

LLM応答からのJSON抽出処理を堅牢化する。現在の実装は `find("{")` と `rfind("}")` による単純な抽出のため、LLMが余分なテキストを追加した場合にパースエラーが発生する。括弧バランス追跡とコードブロック優先抽出により、95%以上の応答を正しくパースできるようにする。

## Technical Context

**Language/Version**: Python 3.11+ (標準ライブラリのみ)
**Primary Dependencies**: なし（標準ライブラリのjson, re モジュール使用）
**Storage**: N/A
**Testing**: pytest（手動テスト + fixtures）
**Target Platform**: Linux (Ubuntu)
**Project Type**: single (既存スクリプトへの機能追加)
**Performance Goals**: 1応答あたり10ms未満
**Constraints**: 標準ライブラリのみ使用、既存APIとの互換性維持
**Scale/Scope**: 単一関数の置き換え（parse_json_response）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | スクリプト内部の改善、Vault構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | 直接影響なし |
| III. Normalization First | ✅ Pass | 正規化プロセスの信頼性向上に寄与 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル判定の信頼性向上に寄与 |
| V. Automation with Oversight | ✅ Pass | 既存の確認フローに影響なし |

**Result**: All gates pass. No violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/005-robust-json-parse/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py    # 修正対象: parse_json_response関数
├── markdown_normalizer.py  # 影響なし
├── tag_extractor.py        # 影響なし
└── tests/
    └── fixtures/           # テストデータ
        ├── tech_document.md  # JSONパースエラーのテストケース
        └── ...
```

**Structure Decision**: 既存の `ollama_normalizer.py` 内の `parse_json_response` 関数を置き換え。新規ファイル作成なし。

## Complexity Tracking

> No constitution violations. Table not required.
