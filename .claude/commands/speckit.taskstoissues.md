---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. From the executed script, extract the path to **tasks.md**.

3. Verify GitHub remote by running:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL

4. Extract repository owner and name from the remote URL.

5. For each task in tasks.md, create a GitHub issue using `gh` CLI:

```bash
gh issue create --repo "owner/repo" --title "Task Title" --body "Task Description"
```

**Issue Format**:
- **Title**: `[Phase N] Task ID - Task Description`
- **Body**: Include task details, dependencies, and acceptance criteria
- **Labels**: Add appropriate labels (e.g., `phase-1`, `tdd`, `setup`)

6. After creating all issues, output a summary with issue numbers and URLs.

> [!CAUTION]
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL

## Notes

- Use `gh` CLI (not GitHub MCP server) for all GitHub operations
- Verify `gh auth status` before creating issues
- If not authenticated, prompt user to run `gh auth login`
