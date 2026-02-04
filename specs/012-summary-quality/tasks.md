# Tasks: Summary品質改善

**Input**: Design documents from `/specs/012-summary-quality/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: テスト明示的に要求されていないため、手動検証タスクのみ含む

**Organization**: US1+US2（P1）は同一実装で対応、US3（P2）は検証フェーズで対応

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

```
.claude/scripts/
├── prompts/stage5_summary.txt        # 新規作成
└── normalizer/
    ├── config.py                     # 変更
    ├── models.py                     # 変更
    └── pipeline/
        ├── stages.py                 # 変更
        └── runner.py                 # 変更
```

---

## Phase 1: Setup (Prompt Definition)

**Purpose**: Stage 5 プロンプトの新規作成

- [X] T001 Create stage5_summary.txt prompt in .claude/scripts/prompts/stage5_summary.txt

**Prompt requirements** (from spec.md):
- 役割設定: ナレッジベースキュレーター
- 言語ルール: 会話言語に合わせる（日本語優先）
- 形式ルール: 箇条書き/構造化、500文字以内、3-5項目
- 禁止事項: "User asked", "Claude said" 等の会話経緯表現
- Good/Bad example 含む
- JSON出力形式: `improved_summary`, `changes_made`

---

## Phase 2: Foundational (Config & Models)

**Purpose**: Stage 5 の基盤設定

**⚠️ CRITICAL**: Phase 3 の実装前に完了必須

- [X] T002 [P] Add stage5_summary entry to STAGE_PROMPTS in .claude/scripts/normalizer/config.py
- [X] T003 [P] Add Stage5Result TypedDict to .claude/scripts/normalizer/models.py

**Stage5Result fields**:
```python
class Stage5Result(TypedDict):
    improved_summary: str
    changes_made: list[str]
```

**Checkpoint**: config と models 準備完了

---

## Phase 3: US1+US2 - Core Implementation (Priority: P1) 🎯 MVP

**Goal**: Stage 5 関数実装とパイプライン統合

**Independent Test**: `python -m normalizer --dry-run` で Summary が日本語化・知識抽出型に変換されることを確認

### Implementation

- [X] T004 [US1][US2] Implement stage5_summary() function in .claude/scripts/normalizer/pipeline/stages.py
- [X] T005 [US1][US2] Add stage5 call after stage4 in .claude/scripts/normalizer/pipeline/runner.py
- [X] T006 [US1][US2] Update post_process() to use stage5 result in .claude/scripts/normalizer/pipeline/stages.py

**stage5_summary() requirements**:
- 入力: `normalized_content`, `filename`, `is_english`
- `## Summary` セクション抽出（正規表現）
- Summary存在時のみLLM呼び出し
- 改善されたSummaryで `normalized_content` を更新
- StageResult返却

**Checkpoint**: MVP完了 - Summary が日本語化・知識抽出型に変換される

---

## Phase 4: US3 - Validation & Enhancement (Priority: P2)

**Goal**: 簡潔さ（500文字以内）の検証と調整

**Independent Test**: 生成されたSummaryの文字数を計測

- [X] T007 [US3] Validate prompt enforces 500-char limit in .claude/scripts/prompts/stage5_summary.txt
- [X] T008 [US3] Manual test with verbose conversation to verify brevity

**Checkpoint**: 全User Story対応完了

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: エッジケース対応と品質向上

- [X] T009 Handle edge case: no Summary section (skip stage5)
- [X] T010 Handle edge case: mixed language conversation
- [X] T011 Run existing test suite: `cd .claude/scripts && python -m pytest normalizer/tests/ -v`
- [X] T012 Manual integration test with sample files from @index/

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1+US2) → Phase 4 (US3) → Phase 5 (Polish)
```

### User Story Mapping

| User Story | Primary Tasks | Description |
|------------|---------------|-------------|
| US1 (P1) | T001, T004-T006 | 日本語Summary生成 |
| US2 (P1) | T001, T004-T006 | 知識抽出型構造 |
| US3 (P2) | T007-T008 | 500文字以内の簡潔さ |

### Parallel Opportunities

```bash
# Phase 2: 並列実行可能
Task: T002 "Add stage5_summary to STAGE_PROMPTS"
Task: T003 "Add Stage5Result TypedDict"
```

---

## Implementation Strategy

### MVP First (Phase 1-3)

1. Complete Phase 1: Prompt作成
2. Complete Phase 2: Config/Models変更
3. Complete Phase 3: Core実装
4. **STOP and VALIDATE**: `--dry-run` で動作確認
5. Deploy if ready

### Incremental Delivery

1. Prompt完成 → Phase 1完了
2. Config/Models → Phase 2完了
3. Core実装 → MVP完了（US1+US2対応）
4. 簡潔さ検証 → US3対応
5. Polish → 全機能完了

---

## Notes

- [P] tasks = 異なるファイル、依存関係なし
- US1とUS2は同一実装で対応（プロンプトの言語・形式ルール）
- US3は検証フェーズで対応（プロンプトの長さ制限）
- Summary セクションがない場合はstage5スキップ
- 既存テストスイートの破壊回避を確認
