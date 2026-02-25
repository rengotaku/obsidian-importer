---
description: "Phase N (TDD/Standard) output format template"
---

# Phase N Output Template

Output format for TDD/Standard Phase. Communicates implementation results to subagents.

**Language**: Japanese

---

```markdown
# Phase N Output: [Phase Name]

**Date**: YYYY-MM-DD
**Status**: Completed | Error
**User Story**: US[N] - [Title]

## Executed Tasks

- [x] T0XX [task description]
- [x] T0XX [task description]
...

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/xxx.py | New | [description] |
| src/yyy.py | Modified | [what changed] |
| tests/test_xxx.py | New | [test coverage] |

## Test Results

```
make test output (excerpt)
...
X passed, Y failed
```

**Coverage**: XX% (target: 80%)

## Discovered Issues

1. **[Issue]**: [description] → [resolution or deferred to Phase N]
2. ...

## Handoff to Next Phase

Items to implement in Phase N+1 ([Story Name]):
- [dependency from this phase]
- [API/interface established]
- Caveats: [caveats]
```
