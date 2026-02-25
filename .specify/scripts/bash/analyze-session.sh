#!/bin/bash
# Session analyzer: Generate human-readable + Claude-analyzable report
# Usage: analyze-session.sh [session_id] [--json] [--output DIR] [--type TYPE]
#
# Options:
#   --json       Output JSON to stdout
#   --output DIR Save reports to directory (creates .json and .md files)
#   --type TYPE  Session type for filename (default: session)

set -euo pipefail

# ============================================================
# Argument parsing
# ============================================================

SESSION_ID=""
OUTPUT_JSON=""
OUTPUT_DIR=""
SESSION_TYPE="session"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      OUTPUT_JSON="--json"
      shift
      ;;
    --output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --output=*)
      OUTPUT_DIR="${1#*=}"
      shift
      ;;
    --type)
      SESSION_TYPE="$2"
      shift 2
      ;;
    --type=*)
      SESSION_TYPE="${1#*=}"
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$SESSION_ID" ]]; then
        SESSION_ID="$1"
      fi
      shift
      ;;
  esac
done

# ============================================================
# Session detection
# ============================================================

PROJECT_DIR=$(pwd)
PROJECT_HASH=$(echo "$PROJECT_DIR" | sed 's|^/|-|; s|/|-|g')
SESSION_DIR="$HOME/.claude/projects/$PROJECT_HASH"

if [[ -z "$SESSION_ID" ]]; then
  # Find most recent session in current project
  SESSION_FILE=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | grep -v 'agent-' | head -1 || true)
  if [[ -z "$SESSION_FILE" ]]; then
    echo "No session files found in: $SESSION_DIR" >&2
    exit 1
  fi
  SESSION_ID=$(basename "$SESSION_FILE" .jsonl)
fi

SESSION_FILE="$SESSION_DIR/$SESSION_ID.jsonl"
SUBAGENT_DIR="$SESSION_DIR/$SESSION_ID/subagents"

if [[ ! -f "$SESSION_FILE" ]]; then
  echo "Session not found: $SESSION_ID" >&2
  exit 1
fi

# ============================================================
# Data extraction
# ============================================================

# Session metadata
START_TIME=$(jq -s '.[0].timestamp' "$SESSION_FILE" | tr -d '"')
END_TIME=$(jq -s '.[-1].timestamp' "$SESSION_FILE" | tr -d '"')

# Tool usage (main session)
MAIN_TOOLS=$(jq -s '
  [.[] | select(.type == "assistant") | .message.content |
   if type == "array" then .[] else . end |
   select(.name?) | {name, input}]
' "$SESSION_FILE")

# File operations
FILE_OPS=$(echo "$MAIN_TOOLS" | jq '
  [.[] | select(.name == "Read" or .name == "Edit" or .name == "Write") |
   {tool: .name, file: .input.file_path}]
')

# Bash commands
BASH_CMDS=$(echo "$MAIN_TOOLS" | jq '
  [.[] | select(.name == "Bash") | .input.command]
')

# Errors
ERRORS=$(jq -s '
  [.[] | select(.type == "user") | .message.content |
   if type == "array" then .[] else empty end |
   select(.type? == "tool_result" and .is_error == true) |
   .content]
' "$SESSION_FILE")

# Subagents (detailed)
SUBAGENTS="[]"
if [[ -d "$SUBAGENT_DIR" ]] && ls "$SUBAGENT_DIR"/*.jsonl >/dev/null 2>&1; then
  SUBAGENTS=$(
    for f in "$SUBAGENT_DIR"/*.jsonl; do
      [[ -f "$f" ]] || continue
      jq -s '
        {
          id: (.[0].agentId // "unknown"),
          slug: (.[0].slug // "unknown"),
          prompt: ((.[0].message.content // "unknown") | if type == "string" then .[0:200] else tostring[0:200] end),
          model: ([.[] | select(.type == "assistant") | .message.model][0] // "unknown"),
          tokens: {
            input: ([.[] | select(.type == "assistant") | .message.usage.input_tokens // 0] | add),
            output: ([.[] | select(.type == "assistant") | .message.usage.output_tokens // 0] | add),
            cache_read: ([.[] | select(.type == "assistant") | .message.usage.cache_read_input_tokens // 0] | add)
          },
          tool_calls: [
            .[] | select(.type == "assistant") | .message.content |
            if type == "array" then .[] else . end |
            select(.name?) |
            {
              tool: .name,
              detail: (
                if .name == "Bash" then .input.command[0:80]
                elif .name == "Read" then .input.file_path
                elif .name == "Edit" then .input.file_path
                elif .name == "Write" then .input.file_path
                elif .name == "WebFetch" then .input.url
                elif .name == "Grep" then .input.pattern
                elif .name == "Glob" then .input.pattern
                elif .name == "Task" then .input.description
                else (.input | tostring)[0:60]
                end
              )
            }
          ],
          errors: [
            .[] | select(.type == "user") | .message.content |
            if type == "array" then .[] else empty end |
            select(.type? == "tool_result" and .is_error == true) |
            .content[0:200]
          ],
          start_time: .[0].timestamp,
          end_time: .[-1].timestamp
        }
      ' "$f"
    done | jq -s '.'
  )
fi

# Tool summary
TOOL_SUMMARY=$(echo "$MAIN_TOOLS" | jq '
  group_by(.name) | map({tool: .[0].name, count: length}) | sort_by(-.count)
')

# ============================================================
# Agent improvement metrics (for insights generation)
# ============================================================

# Duplicate file reads
DUPLICATE_READS=$(echo "$FILE_OPS" | jq '
  [.[] | select(.tool == "Read") | .file] |
  group_by(.) | map(select(length > 1) | {file: .[0], count: length}) |
  sort_by(-.count)
')

# Sequential read patterns (potential parallelization)
SEQUENTIAL_READS=$(echo "$MAIN_TOOLS" | jq '
  [range(0; length-1) as $i |
   select(.[$i].name == "Read" and .[$i+1].name == "Read") |
   {first: .[$i].input.file_path, second: .[$i+1].input.file_path}]
')

# Error patterns
ERROR_PATTERNS=$(echo "$ERRORS" | jq '
  [.[] |
   if test("not found|not available|not installed|ModuleNotFoundError|ImportError"; "i") then "env_dependency"
   elif test("permission denied"; "i") then "permission"
   elif test("timeout|timed out"; "i") then "timeout"
   elif test("syntax|parse"; "i") then "syntax"
   else "other"
   end
  ] | group_by(.) | map({type: .[0], count: length}) | sort_by(-.count)
')

# Preflight-preventable errors count
PREFLIGHT_ERRORS=$(echo "$ERRORS" | jq '
  [.[] | select(test("not found|not available|not installed|ModuleNotFoundError|ImportError"; "i"))] | length
')

# Token totals
TOTAL_INPUT_TOKENS=$(echo "$SUBAGENTS" | jq '[.[] | .tokens.input] | add // 0')
TOTAL_OUTPUT_TOKENS=$(echo "$SUBAGENTS" | jq '[.[] | .tokens.output] | add // 0')
TOTAL_CACHE_TOKENS=$(echo "$SUBAGENTS" | jq '[.[] | .tokens.cache_read] | add // 0')

# Cache hit rate (percentage)
CACHE_HIT_RATE=$(echo "$SUBAGENTS" | jq '
  (([.[] | .tokens.cache_read] | add) // 0) as $cache |
  (([.[] | .tokens.input] | add) // 1) as $input |
  if $input > 0 then ($cache / $input * 100 | floor) else 0 end
')

# Model usage analysis
MODEL_USAGE=$(echo "$SUBAGENTS" | jq '
  group_by(.model) | map({
    model: .[0].model,
    count: length,
    total_output: ([.[] | .tokens.output] | add)
  }) | sort_by(-.count)
')

# ============================================================
# JSON output generation
# ============================================================

generate_json() {
  jq -n \
    --arg session_id "$SESSION_ID" \
    --arg start "$START_TIME" \
    --arg end "$END_TIME" \
    --arg session_type "$SESSION_TYPE" \
    --argjson tool_summary "$TOOL_SUMMARY" \
    --argjson file_ops "$FILE_OPS" \
    --argjson bash_cmds "$BASH_CMDS" \
    --argjson errors "$ERRORS" \
    --argjson subagents "$SUBAGENTS" \
    --argjson duplicate_reads "$DUPLICATE_READS" \
    --argjson sequential_reads "$SEQUENTIAL_READS" \
    --argjson error_patterns "$ERROR_PATTERNS" \
    --argjson preflight_errors "$PREFLIGHT_ERRORS" \
    --argjson total_input_tokens "$TOTAL_INPUT_TOKENS" \
    --argjson total_output_tokens "$TOTAL_OUTPUT_TOKENS" \
    --argjson total_cache_tokens "$TOTAL_CACHE_TOKENS" \
    --argjson cache_hit_rate "$CACHE_HIT_RATE" \
    --argjson model_usage "$MODEL_USAGE" \
    '{
      session: {
        id: $session_id,
        type: $session_type,
        duration: {start: $start, end: $end}
      },
      metrics: {
        tool_summary: $tool_summary,
        tokens: {
          input: $total_input_tokens,
          output: $total_output_tokens,
          cache_read: $total_cache_tokens,
          cache_hit_rate_percent: $cache_hit_rate
        },
        errors: ($errors | length),
        subagents: ($subagents | length)
      },
      details: {
        file_operations: $file_ops,
        bash_commands: $bash_cmds,
        errors: $errors,
        subagents: $subagents
      },
      agent_improvement_hints: {
        duplicate_reads: $duplicate_reads,
        sequential_reads: $sequential_reads,
        error_patterns: $error_patterns,
        preflight_preventable_errors: $preflight_errors,
        model_usage: $model_usage
      }
    }'
}

# ============================================================
# Markdown output generation
# ============================================================

generate_markdown() {
  local timestamp
  timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

  cat <<EOF
# Session Analysis Report

**Generated**: $timestamp
**Session ID**: $SESSION_ID
**Type**: $SESSION_TYPE

## Duration

- **Start**: $START_TIME
- **End**: $END_TIME

## Metrics Summary

| Category | Value |
|----------|-------|
| Tools Used | $(echo "$TOOL_SUMMARY" | jq 'length') types |
| File Operations | $(echo "$FILE_OPS" | jq 'length') |
| Bash Commands | $(echo "$BASH_CMDS" | jq 'length') |
| Errors | $(echo "$ERRORS" | jq 'length') |
| Subagents | $(echo "$SUBAGENTS" | jq 'length') |

## Token Usage

| Metric | Value |
|--------|-------|
| Input Tokens | $TOTAL_INPUT_TOKENS |
| Output Tokens | $TOTAL_OUTPUT_TOKENS |
| Cache Read | $TOTAL_CACHE_TOKENS |
| Cache Hit Rate | ${CACHE_HIT_RATE}% |

## Tool Usage

| Tool | Count |
|------|-------|
$(echo "$TOOL_SUMMARY" | jq -r '.[] | "| \(.tool) | \(.count) |"')

## Subagents

| ID | Model | Tokens (in/out) | Cache | Errors |
|----|-------|-----------------|-------|--------|
$(echo "$SUBAGENTS" | jq -r '.[] | "| \(.id[0:8]) | \(.model | split("-") | .[-1]) | \(.tokens.input)/\(.tokens.output) | \(.tokens.cache_read) | \(.errors | length) |"')

## Error Summary

$(if [[ $(echo "$ERRORS" | jq 'length') -gt 0 ]]; then
  echo "| Type | Count |"
  echo "|------|-------|"
  echo "$ERROR_PATTERNS" | jq -r '.[] | "| \(.type) | \(.count) |"'
else
  echo "_No errors recorded_"
fi)

## Agent Improvement Hints

### Duplicate File Reads

$(if [[ $(echo "$DUPLICATE_READS" | jq 'length') -gt 0 ]]; then
  echo "| File | Read Count |"
  echo "|------|------------|"
  echo "$DUPLICATE_READS" | jq -r '.[] | "| \(.file | split("/") | .[-1]) | \(.count) |"'
else
  echo "_No duplicate reads detected_"
fi)

### Sequential Reads (Parallelization Opportunities)

$(if [[ $(echo "$SEQUENTIAL_READS" | jq 'length') -gt 0 ]]; then
  echo "Found **$(echo "$SEQUENTIAL_READS" | jq 'length')** sequential read patterns that could potentially be parallelized."
else
  echo "_No sequential read patterns detected_"
fi)

### Preflight-Preventable Errors

$(if [[ "$PREFLIGHT_ERRORS" -gt 0 ]]; then
  echo "**$PREFLIGHT_ERRORS** errors could have been prevented with environment pre-checks."
else
  echo "_No preflight-preventable errors_"
fi)

### Model Usage

| Model | Invocations | Total Output |
|-------|-------------|--------------|
$(echo "$MODEL_USAGE" | jq -r '.[] | "| \(.model | split("-") | .[-1]) | \(.count) | \(.total_output) |"')

---

_Use \`--json\` flag or read the corresponding .json file for Claude-based insights generation._
EOF
}

# ============================================================
# Human-readable terminal output
# ============================================================

print_terminal_report() {
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║                    SESSION ANALYSIS REPORT                   ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo ""
  echo "📋 Session: $SESSION_ID"
  echo "📝 Type:    $SESSION_TYPE"
  echo "⏱️  Start:   $START_TIME"
  echo "⏱️  End:     $END_TIME"
  echo ""

  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ 🔧 Tool Usage Summary                                        │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "$TOOL_SUMMARY" | jq -r '.[] | "  \(.tool): \(.count)"'
  echo ""

  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ 💰 Token Usage                                               │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "  Input:      $TOTAL_INPUT_TOKENS"
  echo "  Output:     $TOTAL_OUTPUT_TOKENS"
  echo "  Cache Read: $TOTAL_CACHE_TOKENS"
  echo "  Cache Rate: ${CACHE_HIT_RATE}%"
  echo ""

  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ 📁 File Operations                                           │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "$FILE_OPS" | jq -r '.[] | "  [\(.tool)] \(.file)"' | sort | uniq -c | sort -rn | head -20
  echo ""

  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ 💻 Bash Commands (top 10)                                    │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "$BASH_CMDS" | jq -r '.[]' 2>/dev/null | head -10 | while read -r cmd; do
    echo "  $ ${cmd:0:70}"
  done
  echo ""

  ERROR_COUNT=$(echo "$ERRORS" | jq 'length')
  if [[ "$ERROR_COUNT" -gt 0 ]]; then
    echo "┌──────────────────────────────────────────────────────────────┐"
    echo "│ ❌ Errors ($ERROR_COUNT)                                           │"
    echo "└──────────────────────────────────────────────────────────────┘"
    echo "$ERRORS" | jq -r '.[]' 2>/dev/null | head -5 | while read -r err; do
      echo "  ${err:0:70}..."
    done
    echo ""
  fi

  SUBAGENT_COUNT=$(echo "$SUBAGENTS" | jq 'length')
  if [[ "$SUBAGENT_COUNT" -gt 0 ]]; then
    echo "┌──────────────────────────────────────────────────────────────┐"
    echo "│ 🤖 Subagents ($SUBAGENT_COUNT)                                         │"
    echo "└──────────────────────────────────────────────────────────────┘"
    echo "$SUBAGENTS" | jq -r '
      .[] |
      "  \(.id[0:8]) (\(.slug))",
      "    model: \(.model | split("-") | .[-1])",
      "    tokens: \(.tokens.input) in / \(.tokens.output) out (cache: \(.tokens.cache_read))",
      "    tools: \(.tool_calls | length)",
      (if (.errors | length) > 0 then "    ❌ errors: \(.errors | length)" else empty end),
      ""
    '
  fi

  # Agent improvement hints
  DUP_COUNT=$(echo "$DUPLICATE_READS" | jq 'length')
  SEQ_COUNT=$(echo "$SEQUENTIAL_READS" | jq 'length')
  if [[ "$DUP_COUNT" -gt 0 || "$SEQ_COUNT" -gt 2 || "$PREFLIGHT_ERRORS" -gt 0 ]]; then
    echo "┌──────────────────────────────────────────────────────────────┐"
    echo "│ 🔬 Agent Improvement Hints                                   │"
    echo "└──────────────────────────────────────────────────────────────┘"
    if [[ "$DUP_COUNT" -gt 0 ]]; then
      echo "  ⚠️  Duplicate reads: $DUP_COUNT files read multiple times"
    fi
    if [[ "$SEQ_COUNT" -gt 2 ]]; then
      echo "  ⚠️  Parallelization: $SEQ_COUNT sequential reads could be parallel"
    fi
    if [[ "$PREFLIGHT_ERRORS" -gt 0 ]]; then
      echo "  ⚠️  Preflight: $PREFLIGHT_ERRORS errors preventable with env checks"
    fi
    echo ""
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "💡 Options: --json (JSON output), --output DIR (save files)"
}

# ============================================================
# Main execution
# ============================================================

if [[ -n "$OUTPUT_DIR" ]]; then
  # File output mode
  mkdir -p "$OUTPUT_DIR"
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)

  JSON_FILE="$OUTPUT_DIR/${TIMESTAMP}-${SESSION_TYPE}.json"
  MD_FILE="$OUTPUT_DIR/${TIMESTAMP}-${SESSION_TYPE}.md"

  generate_json > "$JSON_FILE"
  generate_markdown > "$MD_FILE"

  echo "📁 Reports saved:"
  echo "   $JSON_FILE"
  echo "   $MD_FILE"
  echo ""
  echo "💡 Run Claude with --insights to generate improvement analysis"

elif [[ "$OUTPUT_JSON" == "--json" ]]; then
  # JSON to stdout
  generate_json

else
  # Terminal output
  print_terminal_report
fi
