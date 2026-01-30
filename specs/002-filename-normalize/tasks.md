# Tasks: Filename Normalize

**Input**: Design documents from `/specs/002-filename-normalize/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: 手動テストのみ（pytest なし）- テストタスクは含めない

**Organization**: タスクは実装計画の変更点ごとに組織化。単一ファイル修正のため、フェーズは簡略化。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different locations in file, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US4)
- Include exact file paths and line numbers in descriptions

## Path Conventions

- **Target**: `.claude/scripts/ollama_normalizer.py`（単一ファイル修正）
- **Test Files**: `@index/` にテストファイルを作成して手動テスト

---

## Phase 1: Setup

**Purpose**: 既存コードの確認とバックアップ

- [x] T001 Create backup of .claude/scripts/ollama_normalizer.py before modifications
- [x] T002 Verify Ollama is running and gpt-oss:20b model is available

**Checkpoint**: バックアップ完了、Ollama稼働確認

---

## Phase 2: Core Implementation (US1 + US2) 🎯 MVP

**Goal**: 日付除去とハイフン→スペース変換を実現（Ollamaタイトルをファイル名として使用）

**Independent Test**: `@index/2022-10-7-Test-Article.md` を処理し、出力が `テスト記事.md` のような形式になること

### Implementation

- [x] T003 [US1][US2] Add `normalize_filename()` function after `clean_filename()` (L318付近) in .claude/scripts/ollama_normalizer.py
- [x] T004 [US1][US2] Update `NORMALIZER_SYSTEM_PROMPT` to instruct Ollama to generate readable titles (L89-95) in .claude/scripts/ollama_normalizer.py
- [x] T005 [US1][US2] Modify `process_single_file()` to use Ollama-generated title as filename (L475-476) in .claude/scripts/ollama_normalizer.py
- [x] T006 [US1][US2] Add fallback logic when Ollama returns empty title in .claude/scripts/ollama_normalizer.py

**Checkpoint**: 日付除去とスペース区切り変換が動作

---

## Phase 3: Consistency & Safety (US3 + US4)

**Goal**: ファイル名とfrontmatter.titleの整合性、重複処理の確認

**Independent Test**: 処理後のファイルで `head -5` してファイル名とtitleが一致すること

### Implementation

- [x] T007 [US3] Verify filename matches frontmatter.title in build_normalized_file() - no changes needed (existing logic)
- [x] T008 [US4] Verify duplicate handling in get_destination_path() - no changes needed (existing logic)

**Checkpoint**: 整合性と重複処理が正常動作

---

## Phase 4: Validation & Polish

**Purpose**: 手動テストとエッジケース確認

- [x] T009 Create test file: `@index/2022-10-7-Test-Date-Removal.md` with sample content
- [x] T010 Run `python3 .claude/scripts/ollama_normalizer.py --preview "@index/2022-10-7-Test-Date-Removal.md"` and verify output
- [x] T011 Run actual processing and verify file is created with correct filename
- [x] T012 Verify frontmatter.title matches filename
- [x] T013 Test edge case: file with illegal characters in title
- [x] T014 Test edge case: very long filename (>200 chars)
- [x] T015 Test edge case: duplicate filename handling
- [x] T016 Clean up test files from @index/ and destination vaults
- [x] T017 Run quickstart.md validation steps

**Checkpoint**: すべてのテストケースが成功

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Core)**: Depends on Phase 1 - BLOCKS validation
- **Phase 3 (Consistency)**: Depends on Phase 2 - verification only
- **Phase 4 (Validation)**: Depends on Phase 2 and 3

### Task Dependencies

```
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009-T017
                ↓
           (T003-T006 are sequential - same file, related logic)
```

### Parallel Opportunities

- T001 and T002 can run in parallel (different operations)
- T009-T016 validation tests can run sequentially but are independent scenarios

---

## Implementation Strategy

### MVP First (Phase 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Core Implementation
3. **STOP and VALIDATE**: Test with one sample file
4. If working, proceed to Phase 3-4

### Incremental Delivery

1. T001-T002: Setup → Ready to modify
2. T003-T006: Core changes → Basic functionality working
3. T007-T008: Verification → Confirm existing logic handles US3/US4
4. T009-T017: Full validation → Production ready

---

## Summary

| Phase | Tasks | Purpose |
|-------|-------|---------|
| 1. Setup | T001-T002 | Backup and prerequisite check |
| 2. Core (MVP) | T003-T006 | Main functionality (US1+US2) |
| 3. Consistency | T007-T008 | Verification (US3+US4) |
| 4. Validation | T009-T017 | Testing and polish |

**Total Tasks**: 17
**MVP Tasks**: 6 (T001-T006)
**Estimated Effort**: ~30分（単一ファイル、約50行変更）

---

## Notes

- 単一ファイル修正のため、並列実行の機会は限定的
- US3とUS4は既存ロジックで対応済み - 確認のみ
- 手動テストは quickstart.md の手順に従う
- コミットは Phase ごとに実施推奨
