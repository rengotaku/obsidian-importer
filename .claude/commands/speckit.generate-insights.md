---
description: Generate agent improvement insights from session analysis JSON
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Analyze session data and generate actionable agent improvement recommendations.
This is Stage 2 of the session analysis workflow:

1. **Stage 1**: `analyze-session.sh --output DIR` → generates `.json` and `.md`
2. **Stage 2**: This command → reads `.json` → generates `-insights.md`

## Instructions

1. **Locate the JSON file**:
   - If user provides path: use that path
   - Otherwise: find most recent `.json` in `specs/*/analyzed-action/`

2. **Read and parse the JSON file**:
   ```bash
   cat <path-to-json>
   ```

3. **Analyze the following dimensions**:

   ### A. Efficiency Analysis
   - **Duplicate reads**: Files read multiple times → recommend caching or single read
   - **Sequential reads**: Consecutive reads that could be parallelized
   - **Tool usage patterns**: Excessive tool calls, redundant operations

   ### B. Delegation Analysis
   - **Model selection**: Was opus/sonnet/haiku appropriate for task complexity?
     - opus for <2000 output tokens → consider sonnet/haiku
     - haiku for >10000 output tokens → consider sonnet
   - **Subagent utilization**: Were tasks appropriately delegated?
   - **Parallel opportunities**: Independent tasks run sequentially?

   ### C. Error Prevention Analysis
   - **Preflight-preventable**: Environment/dependency errors that could be caught early
   - **Retry patterns**: Same operation retried multiple times
   - **Error recovery**: How well did agents recover from errors?

   ### D. Workflow Adherence
   - **TDD compliance**: RED → GREEN → Verify flow followed?
   - **Commit granularity**: Appropriate commit frequency?
   - **Phase transitions**: Clean handoffs between phases?

   ### E. Cost Efficiency
   - **Token usage**: Input/output ratio, cache utilization
   - **Model cost**: Higher-cost models used appropriately?

4. **Generate insights document** with format:

```markdown
# Session Insights: {session_type}

**Generated**: {timestamp}
**Based on**: {json_file_path}

## Executive Summary

{2-3 sentence summary of key findings}

## Improvement Recommendations

### 🔴 HIGH Priority

{Critical improvements that should be addressed immediately}

### 🟡 MEDIUM Priority

{Important improvements for next session}

### 🟢 LOW Priority

{Nice-to-have optimizations}

## Detailed Analysis

### Efficiency
{Analysis with specific examples from session data}

### Delegation
{Analysis with specific examples from session data}

### Error Prevention
{Analysis with specific examples from session data}

### Cost
{Token usage analysis and recommendations}

## Actionable Next Steps

1. {Specific action item}
2. {Specific action item}
3. {Specific action item}

## Metrics Comparison (if baseline available)

| Metric | This Session | Baseline | Delta |
|--------|-------------|----------|-------|
| ... | ... | ... | ... |
```

5. **Save the insights file**:
   - Same directory as input JSON
   - Filename: replace `.json` with `-insights.md`
   - Example: `20260225-074753-implement.json` → `20260225-074753-implement-insights.md`

## Analysis Guidelines

### Model Selection Recommendations

| Scenario | Current | Recommendation |
|----------|---------|----------------|
| Output < 2000 tokens, used opus | opus | Consider sonnet (cost savings) |
| Output < 500 tokens, used sonnet | sonnet | Consider haiku (cost savings) |
| Complex reasoning, used haiku | haiku | Consider sonnet/opus (quality) |
| Test generation | any | opus recommended (quality critical) |
| Implementation | any | sonnet recommended (balance) |
| Simple tasks | any | haiku recommended (efficiency) |

### Parallelization Opportunities

Look for patterns like:
- Multiple independent file reads
- Independent subagent tasks
- Non-dependent test executions

### Preflight Check Categories

| Error Pattern | Preflight Check |
|---------------|-----------------|
| `ModuleNotFoundError` | `python -c "import X"` |
| `command not found` | `which command` |
| `file not found` | `test -f path` |
| `permission denied` | `test -w path` |

## Output

Write the insights file and confirm:
```
✅ Insights generated: {path-to-insights.md}

Key findings:
- {finding 1}
- {finding 2}
- {finding 3}
```
