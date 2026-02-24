---
description: Create GitHub issue for bugs/improvements found during development
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. **Verify GitHub environment**:
   ```bash
   gh auth status
   git config --get remote.origin.url
   ```
   - If not authenticated, prompt: `gh auth login`
   - If not a GitHub remote, abort

2. **Get current context**:
   ```bash
   git branch --show-current
   ```
   - Extract branch name for reference in issue body

3. **Gather issue details**:
   - If `$ARGUMENTS` is provided, use as title
   - If empty, ask user for:
     - **Title**: Brief description of the issue
     - **Type**: bug / enhancement / question
     - **Description**: Details, reproduction steps, context

4. **Create issue**:
   ```bash
   gh issue create \
     --title "Issue Title" \
     --body "Issue body with context" \
     --label "bug"
   ```

5. **Output result**:
   - Issue number and URL
   - Confirm issue was created

## Issue Body Template

```markdown
## Context

- **Found in branch**: `{branch_name}`
- **Related to**: {current work description}

## Description

{user provided description}

## Reproduction Steps (if bug)

1. ...
2. ...

## Expected vs Actual

- **Expected**: ...
- **Actual**: ...
```

## Usage Examples

```bash
# Quick issue with title only
/speckit.newissue "OAuth token refresh fails silently"

# Interactive mode (no arguments)
/speckit.newissue
```

## Notes

- Use `gh` CLI (not GitHub MCP server)
- Issue body is written in the language user provides
- Add appropriate labels based on issue type:
  - bug → `bug`
  - enhancement → `enhancement`
  - question → `question`
