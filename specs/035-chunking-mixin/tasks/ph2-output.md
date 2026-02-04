# Phase 2 Output: BaseStage Template Method - BLOCKED

**Feature**: 035-chunking-mixin
**Phase**: Phase 2 - Foundational - BaseStage Template Method 追加
**Date**: 2026-01-26
**Status**: BLOCKED - Design Issue Identified

## Summary

Phase 2 partially completed but encountered a critical design issue. Template Method pattern was added to BaseStage as specified, but this causes ALL stages (Extract, Transform, Load) to require abstract method implementations. The chunking pattern should only apply to Extract stages.

##Task Completion

| Task | Status | Description |
|------|--------|-------------|
| T006 | ✅ | Read previous phase output |
| T007 | ✅ | Create test skeleton |
| T008 | ✅ | Implement test assertions |
| T009 | ✅ | Verify RED state |
| T010 | ✅ | Add `_discover_raw_items()` abstract method |
| T011 | ✅ | Add `_build_conversation_for_chunking()` abstract method |
| T012 | ✅ | Add `discover_items()` template method |
| T013 | ✅ | Add `_chunk_if_needed()` protected method |
| T014 | ✅ | Add `_chunker` initialization |
| T015 | ❌ | Tests failing - design issue |
| T016 | ⏸️ | Coverage check - blocked |
| T017 | ⏸️ | Phase output - this document |

## Issue Details

### Problem

Template Method pattern was added to `BaseStage` as per tasks.md specification. However, this forces **ALL** stages (Extract, Transform, Load) to implement the abstract methods:
- `_discover_raw_items()`
- `_build_conversation_for_chunking()`

### Impact

**Affected Stages**:
- ✅ ClaudeExtractor (Extract) - needs abstract methods (expected)
- ✅ ChatGPTExtractor (Extract) - needs abstract methods (expected)
- ✅ GitHubExtractor (Extract) - needs abstract methods (expected)
- ❌ KnowledgeTransformer (Transform) - forced to implement abstract methods (NOT expected)
- ❌ SessionLoader (Load) - forced to implement abstract methods (NOT expected)
- ❌ VaultLoader (Load) - forced to implement abstract methods (NOT expected)

### Root Cause

The Template Method pattern for chunking is **Extract-specific**, but was placed in `BaseStage` which is inherited by all stages (Extract, Transform, Load).

## Files Modified

### Core

- `src/etl/core/stage.py`:
  - Added `BaseStage.__init__(chunk_size)` with `_chunker` initialization
  - Added abstract method `_discover_raw_items(input_path)`
  - Added abstract method `_build_conversation_for_chunking(item)`
  - Added concrete method `discover_items(input_path)` (Template Method)
  - Added protected method `_chunk_if_needed(item)`

### Extractors (Temporary Stubs)

- `src/etl/stages/extract/claude_extractor.py`:
  - Added `super().__init__(chunk_size)` call
  - Added stub implementations of `_discover_raw_items()` and `_build_conversation_for_chunking()`

- `src/etl/stages/extract/chatgpt_extractor.py`:
  - Added stub implementations of abstract methods

- `src/etl/stages/extract/github_extractor.py`:
  - Added `super().__init__()` call
  - Added `steps` property (was missing)
  - Added stub implementations of abstract methods

- `src/etl/stages/extract/file_extractor.py`:
  - Added `super().__init__()` call
  - Added stub implementations of abstract methods

### Tests

- `src/etl/tests/test_stages.py`:
  - Added `TestBaseStageTemplateMethod` test class
  - Added test `test_abstract_method_not_implemented_raises_typeerror` ✅ PASSING
  - Created `TestStageMixin` helper for test stages
  - Updated all test stage classes to use mixin and call `super().__init__()`

## Test Status

**Test Results**: 339 tests, 304 passed, 35 failed, 10 skipped

**New Test (Phase 2)**:
- ✅ `test_abstract_method_not_implemented_raises_typeerror` - PASSING

**Baseline Tests**:
- ✅ All test_stages.py tests - PASSING
- ❌ Transform/Load stage tests - FAILING (require abstract methods)

**Error Pattern**:
```
TypeError: Can't instantiate abstract class KnowledgeTransformer without an
implementation for abstract methods '_build_conversation_for_chunking', '_discover_raw_items'
```

## Proposed Solution

### Option 1: Create BaseExtractor (Recommended)

Create a new `BaseExtractor` class that inherits from `BaseStage` and adds the Template Method pattern:

```python
class BaseStage(ABC):
    # Existing code - NO abstract methods for chunking
    ...

class BaseExtractor(BaseStage):
    """Base class for Extract stages with chunking support."""

    def __init__(self, chunk_size=25000):
        from ..utils.chunker import Chunker
        self._chunker = Chunker(chunk_size=chunk_size)

    @abstractmethod
    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        ...

    @abstractmethod
    def _build_conversation_for_chunking(self, item: ProcessingItem) -> Any | None:
        ...

    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        # Template Method implementation
        ...

    def _chunk_if_needed(self, item: ProcessingItem) -> list[ProcessingItem]:
        # Chunking logic
        ...
```

**Changes Required**:
- Create `src/etl/core/extractor.py` with `BaseExtractor` class
- Move Template Method methods from `BaseStage` to `BaseExtractor`
- Update ClaudeExtractor, ChatGPTExtractor, GitHubExtractor to inherit from `BaseExtractor`
- Remove stub implementations from FileExtractor (not an extractor needing chunking)
- Transform/Load stages continue inheriting from `BaseStage` (no changes needed)

**Pros**:
- Clean separation of concerns
- Transform/Load stages unaffected
- Follows Single Responsibility Principle
- Matches original intent from spec.md

**Cons**:
- Requires creating new file (not in original tasks.md)
- Additional refactoring step

### Option 2: Make Abstract Methods Optional (Not Recommended)

Remove `@abstractmethod` decorator and provide default implementations that return empty results.

**Pros**:
- Minimal code changes
- No new files

**Cons**:
- Violates Template Method pattern (no enforcement)
- Allows feature leakage (new providers can forget to implement methods)
- Fails SC-006 success criterion ("TypeError on missing abstract method")

## Recommendation

**Adopt Option 1 (BaseExtractor)** as it:
1. ✅ Maintains template method enforcement (SC-006)
2. ✅ Prevents feature leakage in new providers
3. ✅ Keeps Transform/Load stages simple
4. ✅ Follows original design intent

## Next Steps

**Decision Required from Parent**:
1. Approve Option 1 (BaseExtractor) - create new file and refactor
2. Approve Option 2 (Make optional) - remove `@abstractmethod` decorators
3. Alternative solution

**If Option 1 Approved**:
1. Create `src/etl/core/extractor.py` with `BaseExtractor`
2. Move Template Method code from `BaseStage` to `BaseExtractor`
3. Update extractors to inherit from `BaseExtractor`
4. Verify 335 baseline tests pass
5. Continue to Phase 3 (ClaudeExtractor refactoring)

## Lessons Learned

- Template Method pattern should be applied at the appropriate abstraction level
- Abstract methods in base classes affect ALL subclasses
- Design review needed before implementation when inheritance hierarchy is complex
- Test-driven development caught the issue early (35 failures vs potential production bug)

## Files for Next Phase

**If proceeding with Option 1**:

**New File**:
- `src/etl/core/extractor.py` - BaseExtractor class

**Files to Modify**:
- `src/etl/core/stage.py` - Remove Template Method code
- `src/etl/stages/extract/claude_extractor.py` - Inherit from BaseExtractor
- `src/etl/stages/extract/chatgpt_extractor.py` - Inherit from BaseExtractor
- `src/etl/stages/extract/github_extractor.py` - Inherit from BaseExtractor
- `src/etl/stages/extract/file_extractor.py` - Revert changes (not an extractor)
- `src/etl/tests/test_stages.py` - Update test for BaseExtractor

## Status

**Phase 2**: ⏸️ PAUSED - Awaiting decision on Option 1 vs Option 2

**Baseline Integrity**: ⚠️ Currently broken (304/335 passing)

**Blocker**: Design decision required before proceeding to Phase 3

