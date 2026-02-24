---
description: "Phase 1 (Setup) output format template"
---

# Phase 1 Output Template

Output format for Setup Phase. Communicates existing code analysis results to subagents.

**Language**: Japanese

---

```markdown
# Phase 1 Output: Setup

**Date**: YYYY-MM-DD
**Status**: Completed | Error

## Executed Tasks

- [x] T001 [task description]
- [x] T002 [task description]
...

## Existing Code Analysis

### [filename.ext]

**Structure**:
- `ClassName`: [purpose]
- `function_name`: [purpose]

**Required Updates**:
1. `function_name`: [current] → [required change]
2. ...

### [another_file.ext]
...

## Existing Test Analysis

- `tests/test_xxx.py`: [what it covers]
- **Does not exist**: tests/test_yyy.py → Create new

**Required Fixtures**:
- `fixture_name`: [purpose]

## Newly Created Files

### [new_file.ext] (skeleton)

- `function_name`: [purpose] (Implement in Phase N)
- `ClassName`: [purpose]

## Technical Decisions

1. **[Decision]**: [rationale]
2. **[Decision]**: [rationale]

## Handoff to Next Phase

Items to implement in Phase 2 ([Story Name]):
- `function_name`: [description]
- Reusable existing code: [what can be reused]
- Caveats: [caveats]
```
