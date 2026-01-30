# Implementation Plan: Extract Stage Discovery 委譲

**Branch**: `031-extract-discovery-delegation` | **Date**: 2026-01-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/031-extract-discovery-delegation/spec.md`

## Summary

ImportPhase の `discover_items()` ロジックを各 Extract stage（ClaudeExtractor, ChatGPTExtractor）に委譲する。これにより、ChatGPT の `mapping` ツリー構造と Claude の `chat_messages` 配列形式の両方を正しく処理できるようになる。

**主要変更**:
1. ImportPhase.discover_items() を ClaudeExtractor に移動
2. ImportPhase.run() を修正し、Extract stage の discover_items() を呼び出す
3. ChatGPTExtractor.discover_items() は既存実装を使用

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: tenacity 8.x, ollama, 標準ライブラリ（json, pathlib, dataclasses）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（ETL パイプライン）
**Performance Goals**: 1000+ 会話を 10 分以内に処理
**Constraints**: 既存テスト 275 件を破壊しない
**Scale/Scope**: 1295 件の ChatGPT 会話、既存 Claude インポートとの互換性維持

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 備考 |
|------|------|------|
| **I. Vault Independence** | ✅ PASS | 変更は ETL パイプラインのみ、Vault 構造に影響なし |
| **II. Obsidian Markdown Compliance** | ✅ PASS | 出力フォーマットは変更なし |
| **III. Normalization First** | ✅ PASS | 正規化プロセスへの影響なし |
| **IV. Genre-Based Organization** | ✅ PASS | ジャンル分類への影響なし |
| **V. Automation with Oversight** | ✅ PASS | 既存の確認フローを維持 |

**Gate Status**: ✅ PASS - 全ての原則に準拠

## Project Structure

### Documentation (this feature)

```text
specs/031-extract-discovery-delegation/
├── spec.md              # 機能仕様
├── plan.md              # 本ファイル
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
├── contracts/           # Phase 1 出力（該当なし - 内部リファクタリング）
└── tasks.md             # Phase 2 出力
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   └── stage.py              # BaseStage（変更なし）
├── phases/
│   └── import_phase.py       # ImportPhase（discover_items 削除、run 修正）
├── stages/
│   └── extract/
│       ├── claude_extractor.py   # discover_items 追加（移植）
│       └── chatgpt_extractor.py  # 既存 discover_items 使用
└── tests/
    └── test_import_phase.py      # テスト調整
```

**Structure Decision**: 既存の src/etl 構造を維持。内部リファクタリングのため、新規ディレクトリは不要。

## Complexity Tracking

憲法違反なし - 追跡不要

## Phase 0: Research

### Research Tasks

本機能は既存コードベースの内部リファクタリングであり、外部依存の調査は不要。

**確認済み事項**:

1. **ChatGPTExtractor.discover_items()** - 既に ZIP から会話を抽出する実装が存在（L203-344）
2. **ImportPhase.discover_items()** - Claude 形式専用のロジック（L125-310）
3. **BaseStage.run()** - items: Iterator[ProcessingItem] を受け取る（L254-317）

### Design Decision

| 項目 | 決定 | 理由 |
|------|------|------|
| discover 委譲方式 | ImportPhase が Extract stage の discover_items() を呼び出す | BaseStage.run() のシグネチャ変更を避ける |
| ClaudeExtractor 実装 | ImportPhase の _expand_conversations() を移植 | ロジック重複を避け、単一責任を維持 |
| テスト戦略 | 既存テストを維持し、新規テストを追加 | リグレッション防止 |

## Phase 1: Design

### Data Model

本機能は新しいデータモデルを導入しない。既存の ProcessingItem を使用。

### API Contracts

内部リファクタリングのため、外部 API は変更なし。

### Interface Changes

```python
# ClaudeExtractor に追加
class ClaudeExtractor(BaseStage):
    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Claude エクスポートから会話を発見する。

        ImportPhase._expand_conversations() のロジックを移植。
        """
        ...

# ImportPhase.run() の変更
class ImportPhase:
    def run(self, phase_data, debug_mode=False, limit=None) -> PhaseResult:
        extract_stage = self.create_extract_stage()
        # 変更: self.discover_items() → extract_stage.discover_items()
        items = extract_stage.discover_items(input_path)
        extracted = extract_stage.run(ctx, items)
        ...
```

## Implementation Phases

### Phase 1: ClaudeExtractor に discover_items() を追加

**目標**: ImportPhase の discover ロジックを ClaudeExtractor に移植

**タスク**:
1. ImportPhase._expand_conversations() を ClaudeExtractor.discover_items() として移植
2. ImportPhase._build_conversation_for_chunking() を ClaudeExtractor に移植
3. ImportPhase._chunk_conversation() を ClaudeExtractor に移植
4. ClaudeExtractor のユニットテストを追加

### Phase 2: ImportPhase.run() を修正

**目標**: Extract stage の discover_items() を呼び出すように変更

**タスク**:
1. ImportPhase.run() を修正: extract_stage.discover_items() を使用
2. ImportPhase.discover_items() を削除（または非推奨化）
3. 関連ヘルパーメソッドを削除/移動
4. 既存テストの調整

### Phase 3: 統合テストと検証

**目標**: 両プロバイダーでの動作確認

**タスク**:
1. ChatGPT エクスポートでのインポートテスト
2. Claude エクスポートでのインポートテスト
3. 275 件の既存テストがパスすることを確認
4. ドキュメント更新

## Risk Assessment

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 既存テストの破壊 | 高 | 小さな変更を段階的にコミット |
| Claude インポートのリグレッション | 高 | 変更前後の出力を比較 |
| チャンキングロジックの移植ミス | 中 | ユニットテストで網羅的にカバー |

## Next Steps

1. `/speckit.tasks` で詳細タスクを生成
2. Phase 1 から実装開始
3. 各 Phase 完了後にテスト実行で検証
