---
description: Analyze session and generate agent improvement insights
---

## User Input

```text
$ARGUMENTS
```

## Overview

Two-stage session analysis workflow with **automatic file output**:

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: analyze-session.sh --output DIR --type TYPE       │
│   └→ {timestamp}-{type}.json (raw data + metrics)          │
│   └→ {timestamp}-{type}.md (statistics summary)            │
├─────────────────────────────────────────────────────────────┤
│ Stage 2: Claude reads JSON → generates insights            │
│   └→ {timestamp}-{type}-insights.md (improvement proposals) │
└─────────────────────────────────────────────────────────────┘
```

## Instructions

### 1. Determine Output Directory (REQUIRED)

**Always save reports to a file.** Use `check-prerequisites.sh` to get FEATURE_DIR from current branch:

```bash
# Get FEATURE_DIR from current git branch
# Try local script first, then global
FEATURE_DIR=$(.specify/scripts/bash/check-prerequisites.sh --paths-only 2>/dev/null | grep "^FEATURE_DIR:" | cut -d: -f2 | tr -d ' ')

# Fallback to global script if local failed
if [ -z "$FEATURE_DIR" ]; then
  FEATURE_DIR=$($HOME/.claude/scripts/check-prerequisites.sh --paths-only 2>/dev/null | grep "^FEATURE_DIR:" | cut -d: -f2 | tr -d ' ')
fi

# Fallback to branch name
if [ -z "$FEATURE_DIR" ] || [ ! -d "$FEATURE_DIR" ]; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  if [ -n "$BRANCH" ] && [ -d "specs/$BRANCH" ]; then
    FEATURE_DIR="specs/$BRANCH"
  fi
fi

# Set output directory
if [ -n "$FEATURE_DIR" ] && [ -d "$FEATURE_DIR" ]; then
  OUTPUT_DIR="${FEATURE_DIR}/analyzed-action"
else
  OUTPUT_DIR="./analyzed-action"
fi

mkdir -p "$OUTPUT_DIR"
echo "OUTPUT_DIR=$OUTPUT_DIR"
```

### 2. Detect Session Type

Infer from context:
- After `speckit.implement` → `implement`
- After `speckit.plan` → `plan`
- After `speckit.tasks` → `tasks`
- Default → `session`

### 3. Run Stage 1: Data Collection (REQUIRED)

**Always run with `--output`:**

```bash
# Prefer local script, fallback to global
SCRIPT=".specify/scripts/bash/analyze-session.sh"
[[ ! -f "$SCRIPT" ]] && SCRIPT="$HOME/.claude/scripts/analyze-session.sh"

# ALWAYS output to file
$SCRIPT --output "$OUTPUT_DIR" --type "$SESSION_TYPE"
```

This generates:
- `{timestamp}-{type}.json` - Raw data for insights
- `{timestamp}-{type}.md` - Human-readable summary

### 4. Display Terminal Summary

Also run without `--output` to show immediate feedback to user:

```bash
$SCRIPT --type "$SESSION_TYPE"
```

### 5. Run Stage 2: Generate Insights (REQUIRED)

Read the JSON file and generate improvement recommendations:

1. Read the generated `.json` file
2. Analyze using the categories below
3. Write `{timestamp}-{type}-insights.md` to the same directory

**Insights Analysis Categories:**

| Category | What to Check |
|----------|---------------|
| **Efficiency** | Duplicate reads, parallelization opportunities, redundant operations |
| **Delegation** | Model selection appropriateness, subagent utilization |
| **Error Prevention** | Preflight-preventable errors, retry patterns |
| **Workflow** | TDD compliance, commit granularity, phase transitions |
| **Cost** | Token usage efficiency, cache hit rate |

### 6. Report Completion

Show user:
```
✅ Session analysis complete

📁 Output files:
   - {path}/20260225-101756-implement.json
   - {path}/20260225-101756-implement.md
   - {path}/20260225-101756-implement-insights.md

📊 Key findings:
   - {finding 1}
   - {finding 2}
```

## Output Files

| File | Content | Generator |
|------|---------|-----------|
| `{ts}-{type}.json` | Raw metrics, tool usage, errors | Script |
| `{ts}-{type}.md` | Statistics tables, summary | Script |
| `{ts}-{type}-insights.md` | Agent improvement recommendations | Claude |

## Usage

```bash
# Default: full analysis with file output + insights
/speckit.analyze-session

# Analyze specific session
/speckit.analyze-session <session-id>

# Skip insights generation
/speckit.analyze-session --no-insights
```

## Insights Template

Use this structure for `-insights.md`:

```markdown
# Session Insights: {type}

**Generated**: {timestamp}
**Session**: {session_id}

## Executive Summary
{2-3 sentence summary}

## 🔴 HIGH Priority Improvements
{Critical issues}

## 🟡 MEDIUM Priority Improvements
{Important optimizations}

## 🟢 LOW Priority Improvements
{Nice-to-have}

## Detailed Analysis
### Efficiency
### Delegation
### Error Prevention
### Cost

## Actionable Next Steps
1. ...
2. ...
```
