# Implementation Plan: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Branch**: `063-ollama-exception-refactor` | **Date**: 2026-03-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/063-ollama-exception-refactor/spec.md`

## Summary

`call_ollama` 関数をタプル返却から例外ベースに変更し、Python の `contextvars` を使用してパーティション処理単位で file_id をログに自動追加する仕組みを導入する。これにより、エラー発生時のファイル特定が容易になり、新規コードも自動的に file_id 付きログに対応する。

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml で `requires-python = ">=3.11"`)
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets>=9.0, PyYAML>=6.0, requests>=2.28
**Storage**: ファイルシステム (Markdown, JSON, JSONL) - Kedro PartitionedDataset
**Testing**: unittest + coverage (fail_under=80)
**Target Platform**: Linux (ローカル開発環境のみ)
**Project Type**: Single project (Kedro パイプライン)
**Performance Goals**: N/A (バッチ処理、リアルタイム要件なし)
**Constraints**: なし (ローカル専用ツール)
**Scale/Scope**: 個人利用、数千ファイル規模

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Review alignment with constitution principles (`.specify/memory/constitution.md`):

- [x] **Simplicity**: Does this design favor simplicity over complexity?
  - contextvars は Python 標準ライブラリ、追加依存なし
  - カスタムフォーマッターは logging 標準機能の拡張
  - 例外クラスは Python 標準パターン

- [x] **Breaking Changes**: Are breaking changes documented and justified?
  - `call_ollama` の戻り値が `tuple[str, str | None]` → `str` に変更
  - 後方互換性は考慮しない方針に従う
  - すべての呼び出し元を同時に更新

- [x] **Testing**: Are test requirements clearly defined?
  - 80% カバレッジ維持
  - 例外クラスのユニットテスト追加
  - ログコンテキスト機能のユニットテスト追加
  - 既存テストの更新

- [x] **Code Quality**: Are linting requirements addressed?
  - ruff + pylint チェック必須
  - 型ヒント付きで実装

- [x] **Idempotency**: Are operations designed to be idempotent?
  - ログ出力のみ、データ変換には影響なし
  - 既存の冪等性に影響なし

- [x] **Traceability**: Is data lineage tracked?
  - file_id がログに自動追加される
  - エラー発生時のファイル特定が容易に

## Project Structure

### Documentation (this feature)

```text
specs/063-ollama-exception-refactor/
├── spec.md              # 仕様書 (完了)
├── plan.md              # このファイル
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
└── tasks.md             # Phase 2 出力 (/speckit.tasks)
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── utils/
│   ├── log_context.py        # 新規: contextvars + カスタムフォーマッター
│   ├── ollama.py             # 変更: 例外クラス追加、call_ollama 変更
│   └── knowledge_extractor.py # 変更: 呼び出し元更新 (2箇所)
├── pipelines/
│   ├── extract_claude/nodes.py   # 変更: file_id コンテキスト設定
│   ├── extract_openai/nodes.py   # 変更: file_id コンテキスト設定
│   ├── organize/nodes.py         # 変更: 呼び出し元更新 (3箇所) + 手動プレフィックス削除
│   └── transform/nodes.py        # 変更: file_id コンテキスト設定

conf/base/
└── logging.yml           # 変更: カスタムフォーマッター設定

tests/
├── utils/
│   ├── test_log_context.py   # 新規: ログコンテキストのテスト
│   ├── test_ollama_*.py      # 変更: 例外ベースに更新
│   └── test_knowledge_extractor.py  # 変更: 例外ベースに更新
└── pipelines/
    └── organize/test_nodes.py  # 変更: 例外ベースに更新
```

**Structure Decision**: 既存の Kedro プロジェクト構造を維持。新規ファイルは `src/obsidian_etl/utils/log_context.py` のみ。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし。すべての原則に適合。
