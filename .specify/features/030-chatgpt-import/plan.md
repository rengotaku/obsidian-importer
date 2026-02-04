# Implementation Plan: ChatGPT エクスポートインポート

**Branch**: `030-chatgpt-import` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/030-chatgpt-import/spec.md`

## Summary

ChatGPT エクスポート ZIP ファイルを解析し、既存の ETL パイプライン（Transform/Load）を再利用して Obsidian Markdown ノートを生成する。新規実装は Extract ステージ（chatgpt_extractor.py）と CLI の `--provider` オプションのみ。

## Technical Context

**Language/Version**: Python 3.13（既存 ETL 環境）
**Primary Dependencies**: tenacity 8.x（既存）、ollama（既存）、zipfile（標準ライブラリ）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（既存 src/etl 構造を拡張）
**Performance Goals**: 1295 会話を 2 時間以内に処理
**Constraints**: ZIP 展開は一時ディレクトリで行い処理後削除
**Scale/Scope**: 1295 会話、約 100MB の conversations.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | 変更なし - 既存のジャンル振り分けを使用 |
| II. Obsidian Markdown Compliance | ✅ PASS | 既存の Transform/Load を再利用 |
| III. Normalization First | ✅ PASS | frontmatter 正規化は既存ステージで処理 |
| IV. Genre-Based Organization | ✅ PASS | 既存のジャンル判定ロジックを使用 |
| V. Automation with Oversight | ✅ PASS | 既存の確認フローを継承 |

**Gate Result**: ✅ ALL PASS - Phase 0 に進行可能

## Project Structure

### Documentation (this feature)

```text
specs/030-chatgpt-import/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - CLI tool)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/etl/
├── stages/
│   └── extract/
│       ├── claude_extractor.py     # 既存
│       └── chatgpt_extractor.py    # 新規
├── phases/
│   └── import_phase.py             # 修正: provider 分岐追加
├── utils/
│   └── zip_handler.py              # 新規: ZIP 展開ユーティリティ
├── cli.py                          # 修正: --provider オプション追加
└── tests/
    └── test_chatgpt_extractor.py   # 新規

tests/
└── unit/
    └── test_chatgpt_extractor.py   # ユニットテスト
```

**Structure Decision**: 既存の `src/etl/` 構造を拡張。新規ファイルは最小限（Extractor + ZipHandler）。

## Complexity Tracking

> 違反なし - 既存構造を拡張するのみ

## Phase 0: Research Summary

### R1: ChatGPT mapping ツリー構造の走査方法

**Decision**: `current_node` から `parent` を辿って逆順でメッセージを収集

**Rationale**: ChatGPT の会話はツリー構造で、ユーザーの編集により分岐が発生する。`current_node` が最終的な会話の終端を示すため、そこから逆順に辿るのが最も確実。

**Algorithm**:
```python
def traverse_messages(mapping: dict, current_node: str) -> list[dict]:
    messages = []
    node_id = current_node
    while node_id:
        node = mapping.get(node_id, {})
        if node.get('message'):
            messages.append(node['message'])
        node_id = node.get('parent')
    return list(reversed(messages))
```

### R2: ZIP 展開戦略

**Decision**: Python 標準ライブラリ `zipfile` + `tempfile` を使用

**Rationale**:
- 外部依存なし
- メモリ効率: `zipfile.ZipFile.read()` でファイルごとに読み込み可能
- 一時ディレクトリは `tempfile.TemporaryDirectory()` で自動クリーンアップ

### R3: provider 切り替え設計

**Decision**: `ImportPhase` に `provider` パラメータを追加し、Extractor を動的に選択

**Rationale**:
- 最小限の変更
- 既存の Claude インポートに影響なし
- 将来的に Gemini 等も追加可能

**Implementation**:
```python
class ImportPhase:
    def __init__(self, provider: str = "claude", ...):
        self._provider = provider

    def create_extract_stage(self) -> BaseStage:
        if self._provider == "openai":
            return ChatGPTExtractor()
        return ClaudeExtractor()
```

### R4: メッセージロール変換

**Decision**: `author.role` を既存の `sender` 形式に変換

| ChatGPT | Claude | 処理 |
|---------|--------|------|
| user | human | 変換 |
| assistant | assistant | そのまま |
| system | - | 除外 |
| tool | - | 除外 |

### R5: タイムスタンプ変換

**Decision**: Unix timestamp (float) → ISO 8601 → YYYY-MM-DD

```python
from datetime import datetime, timezone

def convert_timestamp(ts: float) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")
```

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md)

### Contracts

N/A - CLI ツールのため API コントラクト不要

### Quickstart

See [quickstart.md](./quickstart.md)

## Implementation Phases

### Phase 1: Core Extraction (P1 Stories)

**Goal**: ZIP → Markdown 基本パイプライン

| Task | Description | Est. |
|------|-------------|------|
| T1.1 | `zip_handler.py` 作成 | S |
| T1.2 | `chatgpt_extractor.py` 作成 | M |
| T1.3 | `import_phase.py` に provider 分岐追加 | S |
| T1.4 | `cli.py` に `--provider` オプション追加 | S |
| T1.5 | ユニットテスト作成 | M |

### Phase 2: Integration (P2 Stories)

**Goal**: 既存機能との統合

| Task | Description | Est. |
|------|-------------|------|
| T2.1 | MIN_MESSAGES スキップロジック | S |
| T2.2 | file_id 重複検出 | S |
| T2.3 | 統合テスト作成 | M |
| T2.4 | 回帰テスト（Claude インポート） | S |

### Phase 3: Polish (P3 Stories)

**Goal**: エッジケース対応

| Task | Description | Est. |
|------|-------------|------|
| T3.1 | マルチモーダルプレースホルダー | S |
| T3.2 | タイトルなし会話の処理 | S |
| T3.3 | ドキュメント更新（CLAUDE.md） | S |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| mapping ツリーの複雑なケース | Medium | Low | 十分なテストケース作成 |
| 大規模 ZIP のメモリ使用量 | Low | Medium | ストリーミング処理で対応済み |
| Ollama タイムアウト | Medium | Low | 既存のリトライ機構を使用 |
