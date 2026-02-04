# Implementation Plan: チャンク処理の共通化

**Branch**: `035-chunking-mixin` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/035-chunking-mixin/spec.md`

## Summary

全 Extractor（Claude, ChatGPT, GitHub）で大きな会話を自動的にチャンク分割する機能を実装。Template Method パターンを BaseStage に組み込み、新規プロバイダー追加時の機能漏れを構造的に防止する。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（既存）、標準ライブラリ（abc, dataclasses, json, pathlib）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）- セッションフォルダ構造
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project
**Performance Goals**: 大規模会話（298,622 文字）を 12 チャンク以下で処理
**Constraints**: LLM タイムアウト回避（25,000 文字/チャンク）
**Scale/Scope**: 1,295 会話（ChatGPT エクスポート基準）、27 件の失敗解消

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | 出力は Vaults への影響なし（ETL パイプライン内部） |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力 Markdown は既存フォーマット維持 |
| III. Normalization First | ✅ Pass | チャンク分割後も frontmatter 正規化適用 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル判定は後続 Stage で実行 |
| V. Automation with Oversight | ✅ Pass | チャンク分割は `--chunk` でオプトイン、デフォルト無効 |

**Re-check after Phase 1**: ✅ All principles maintained in design.

## Project Structure

### Documentation (this feature)

```text
specs/035-chunking-mixin/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   └── stage.py         # BaseStage 拡張（Template Method 追加）
├── stages/
│   └── extract/
│       ├── __init__.py          # Extractor エクスポート
│       ├── claude_extractor.py  # リファクタリング（抽象メソッド実装）
│       ├── chatgpt_extractor.py # リファクタリング（抽象メソッド実装）
│       └── github_extractor.py  # リファクタリング（抽象メソッド実装）
├── utils/
│   └── chunker.py       # 既存（変更なし）
├── cli.py               # --chunk オプション追加
└── tests/
    ├── test_stages.py   # BaseStage チャンク処理テスト
    └── test_chunking_integration.py  # 統合テスト（新規）
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。BaseStage への Template Method 追加と、各 Extractor のリファクタリング。

## Complexity Tracking

> 複雑性の追加なし。Template Method パターンは Python 標準の ABC で実現。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |

## Implementation Phases

### Phase 1: BaseStage Template Method 追加

**Goal**: BaseStage にチャンク処理の Template Method を追加

**Changes**:
1. `src/etl/core/stage.py`:
   - `discover_items()` を concrete method として追加
   - `_discover_raw_items()` を abstract method として追加
   - `_chunk_if_needed()` を protected method として追加
   - `_build_conversation_for_chunking()` を abstract method として追加
   - `_chunker` インスタンスを初期化

**Tests**:
- 抽象メソッド未実装時の TypeError 検証
- チャンク閾値超過時の分割動作検証

### Phase 2: ClaudeExtractor リファクタリング

**Goal**: ClaudeExtractor を新しい Template Method パターンに移行

**Changes**:
1. `src/etl/stages/extract/claude_extractor.py`:
   - `discover_items()` を削除（BaseStage に委譲）
   - `_discover_raw_items()` を実装（既存 `_expand_conversations()` ロジック移植）
   - `_build_conversation_for_chunking()` は既存実装を維持
   - `_chunk_conversation()` を削除（BaseStage `_chunk_if_needed()` に統合）

**Tests**:
- 既存テストがすべてパスすること
- 大きな会話のチャンク分割動作が変わらないこと

### Phase 3: ChatGPTExtractor チャンク対応

**Goal**: ChatGPTExtractor にチャンク処理を追加

**Changes**:
1. `src/etl/stages/extract/chatgpt_extractor.py`:
   - `discover_items()` を削除（BaseStage に委譲）
   - `_discover_raw_items()` を実装（ZIP 展開 + conversations.json パース）
   - `_build_conversation_for_chunking()` を実装（ChatGPT mapping → ConversationProtocol）

**Tests**:
- 298,622 文字会話のチャンク分割検証
- 25,000 文字未満会話の非分割検証

### Phase 4: GitHubExtractor チャンク対応

**Goal**: GitHubExtractor を Template Method パターンに準拠

**Changes**:
1. `src/etl/stages/extract/github_extractor.py`:
   - `discover_items()` を削除（BaseStage に委譲）
   - `_discover_raw_items()` を実装（既存ロジック移植）
   - `_build_conversation_for_chunking()` を実装（常に `None` 返却 = チャンク不要）

**Tests**:
- 既存テストがすべてパスすること
- チャンク処理がスキップされることの検証

### Phase 5: CLI オプション追加

**Goal**: `--chunk` オプションでチャンク分割を有効化（デフォルト無効）

**Changes**:
1. `src/etl/cli.py`:
   - `import` サブコマンドに `--chunk` オプション追加
   - オプション値を Phase/Stage に伝播

2. `Makefile`:
   - `CHUNK=1` 変数サポート

3. `src/etl/stages/transform/knowledge_transformer.py`:
   - デフォルト（チャンク無効）時、閾値超過ファイルは LLM 処理をスキップ
   - スキップ理由を metadata に記録（`skipped_reason: "exceeds_chunk_threshold"`）
   - 次の step は継続実行（エラーで止まらない）

4. `src/etl/stages/load/session_loader.py`:
   - 閾値超過でスキップされたファイルの frontmatter に `too_large: true` を追記

**Tests**:
- デフォルト時に大きな会話が分割されないこと
- デフォルト + 閾値超過ファイル → LLM スキップ、status=SKIPPED、frontmatter に `too_large: true`
- `--chunk` 指定時に閾値超過ファイルが分割されること
- スキップ後も後続アイテムが正常処理されること

### Phase 6: 統合テスト・検証

**Goal**: 全プロバイダーでの動作検証

**Tests**:
1. ChatGPT インポートで 27 件の失敗会話が正常処理されること（SC-001）
2. 298,622 文字会話が 12 チャンク以下に分割されること（SC-002）
3. ClaudeExtractor リファクタリング後、既存テストがパスすること（SC-004）
4. 新規プロバイダーで抽象メソッド未実装時に TypeError（SC-006）

## Dependencies

```
Phase 1 (BaseStage) ← Phase 2 (Claude) ← Phase 6 (Integration)
                   ← Phase 3 (ChatGPT) ←
                   ← Phase 4 (GitHub)  ←
                   ← Phase 5 (CLI)     ←
```

Phase 2-5 は Phase 1 完了後、並行実行可能。Phase 6 は全て完了後。

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 既存 ClaudeExtractor テスト破壊 | High | Phase 2 で段階的移行、テスト先行 |
| ChatGPT mapping 構造の複雑さ | Medium | 既存 Steps ロジックを参考に実装 |
| パフォーマンス劣化 | Low | Chunker は既存実装、オーバーヘッド最小 |
