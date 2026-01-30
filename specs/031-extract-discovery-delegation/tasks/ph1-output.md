# Phase 1 Output: Setup

**Date**: 2026-01-23
**Status**: Completed

## T001: Baseline Test Verification

**Result**: PASSED

```
Ran 275 tests in 13.832s

OK (skipped=8)
```

- All 275 tests passed
- 8 tests skipped (expected - integration tests disabled, removed methods)
- No failures or errors

## T002: ClaudeExtractor Structure Review

### Current Structure

**File**: `src/etl/stages/extract/claude_extractor.py`

```
ClaudeExtractor (BaseStage)
├── __init__(self, steps)
├── stage_type -> StageType.EXTRACT
├── steps -> [ParseJsonStep, ValidateStructureStep]
└── (inherited) run(ctx, items)

ParseJsonStep (BaseStep)
├── name -> "parse_json"
├── process(item) -> ProcessingItem
└── validate_input(item) -> bool

ValidateStructureStep (BaseStep)
├── name -> "validate_structure"
├── process(item) -> ProcessingItem
└── _validate_conversation(data) -> bool
```

### Key Observations

1. **No `discover_items()` method** - ClaudeExtractor currently lacks item discovery
2. **ParseJsonStep handles pre-loaded content** - Already supports content set from discover_items
3. **Simple step pipeline** - Only parse_json and validate_structure

### Comparison with ChatGPTExtractor

**File**: `src/etl/stages/extract/chatgpt_extractor.py`

| Feature | ClaudeExtractor | ChatGPTExtractor |
|---------|-----------------|------------------|
| `discover_items()` | Missing | Present (returns `list[ProcessingItem]`) |
| Input type | JSON files | ZIP file |
| Steps | ParseJsonStep, ValidateStructureStep | ParseZipStep, ValidateStructureStep |
| Chunking | N/A | N/A (no chunking support) |

### ImportPhase Discovery Logic (to be migrated)

**File**: `src/etl/phases/import_phase.py`

Current discover logic in ImportPhase (lines 125-309):
- `discover_items(input_path)` - Entry point
- `_expand_conversations(json_file)` - Parse conversations.json
- `_build_conversation_for_chunking(conv)` - Build SimpleConversation
- `_chunk_conversation(conv, ...)` - Split large conversations

**Dependencies**:
- `SimpleMessage` dataclass (lines 38-47)
- `SimpleConversation` dataclass (lines 50-70)
- `Chunker` from `src/etl/utils/chunker.py`
- `generate_file_id` from `src/etl/utils/file_id.py`

### run() Method Analysis

**ImportPhase.run()** (lines 311-416):
- Line 350: `items = self.discover_items(input_path)` - Uses self.discover_items()
- Discovery is provider-agnostic (uses self.discover_items())
- Does NOT delegate to extract_stage.discover_items()

### Problem Identified

The current `ImportPhase.run()` uses `self.discover_items()` which is hardcoded for Claude format. For ChatGPT, this means:
1. `discover_items()` looks for `conversations.json` in a directory
2. ChatGPT input is a ZIP file, not a directory
3. ChatGPTExtractor.discover_items() exists but is never called

**Solution (Phase 2)**: Change `ImportPhase.run()` to call `extract_stage.discover_items()` instead of `self.discover_items()`.

## Summary for Next Phase

### Phase 2 Prerequisites

1. ChatGPTExtractor.discover_items() exists and returns `list[ProcessingItem]`
2. ClaudeExtractor.discover_items() is missing - needs implementation
3. ImportPhase.run() must delegate to extract_stage.discover_items()

### Action Items for Phase 2

1. Modify ImportPhase.run() line 350 to use extract_stage.discover_items()
2. Handle return type difference: Claude needs Iterator, ChatGPT returns list
3. Test ChatGPT import with the new delegation

### Files to Modify

| File | Changes |
|------|---------|
| `src/etl/phases/import_phase.py` | Line 350: delegate to extract_stage |
| `src/etl/stages/extract/chatgpt_extractor.py` | (Optional) Change return type to Iterator |
