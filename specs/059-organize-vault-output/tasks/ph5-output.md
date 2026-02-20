# Phase 5 Output: US5 Increment Mode

**Date**: 2026-02-20
**Phase**: User Story 5 (競合別名保存)
**Status**: COMPLETED

## Completed Tasks

- [x] T055 Read previous phase output
- [x] T056 test_find_incremented_path_first
- [x] T057 test_find_incremented_path_second
- [x] T058 test_copy_to_vault_increment_existing
- [x] T059 Verify `make test` FAIL (RED)
- [x] T060 Generate RED output
- [x] T061 Read RED tests
- [x] T062 Implement find_incremented_path()
- [x] T063 Add increment mode to copy_to_vault()
- [x] T064 Verify `make test` PASS (GREEN)
- [x] T065 Verify all tests pass (no regressions)
- [x] T066 Generate phase output

## Test Results

```
Ran 424 tests in 5.542s
OK
```

## Implementation Details

### find_incremented_path()

```python
def find_incremented_path(dst: Path) -> Path:
    """Find next available incremented path.

    file.md → file_1.md → file_2.md → ...
    """
    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent

    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1
```

### copy_to_vault() Changes

Added increment handling:
```python
elif conflict_handling == "increment":
    full_path = find_incremented_path(full_path)
    is_incremented = True
```

Added status differentiation:
```python
if is_incremented:
    status = "incremented"
elif file_exists and conflict_handling == "overwrite":
    status = "overwritten"
else:
    status = "copied"
```

### log_copy_summary() Changes

Added incremented tracking:
```python
incremented = sum(1 for r in copy_results if r["status"] == "incremented")
return {
    "total": total,
    "copied": copied,
    "overwritten": overwritten,
    "incremented": incremented,  # NEW
    "skipped": skipped,
    "errors": errors,
}
```

## Checkpoint Verification

`kedro run --pipeline=organize_to_vault --params='{"organize.conflict_handling": "increment"}'` now:
- Creates file_1.md when file.md exists
- Creates file_2.md when file.md and file_1.md exist
- Returns status "incremented" for new files
- Logs incremented count in summary

## All User Stories Complete

| US | Description | Status |
|----|-------------|--------|
| US1 | Preview（出力先確認） | ✅ |
| US2 | Vault へのコピー | ✅ |
| US3 | 競合スキップ (skip) | ✅ |
| US4 | 競合上書き (overwrite) | ✅ |
| US5 | 競合別名保存 (increment) | ✅ |

## Next Phase

Phase 6: Polish & Cross-Cutting Concerns (NO TDD)
