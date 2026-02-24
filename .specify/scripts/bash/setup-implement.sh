#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            echo ""
            echo "Analyzes tasks.md and creates phase output files in FEATURE_DIR."
            echo "Output files are created from .specify/templates/ with final names."
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure directories exist
mkdir -p "$FEATURE_DIR/tasks"
mkdir -p "$FEATURE_DIR/red-tests"

# Template source directory
TEMPLATE_SRC="$REPO_ROOT/.specify/templates"

# Check if tasks.md exists
TASKS_FILE="$FEATURE_DIR/tasks.md"
if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Error: tasks.md not found at $TASKS_FILE" >&2
    exit 1
fi

# Parse phases from tasks.md
# Extract: Phase number, type (setup/tdd/standard), whether it has TDD sections
parse_phases() {
    local tasks_file="$1"
    local phases=()
    local current_phase=""
    local has_tdd=false

    while IFS= read -r line; do
        # Match "## Phase N:" pattern
        if [[ "$line" =~ ^##[[:space:]]+Phase[[:space:]]+([0-9]+): ]]; then
            # Save previous phase if exists
            if [[ -n "$current_phase" ]]; then
                phases+=("$current_phase:$has_tdd")
            fi
            current_phase="${BASH_REMATCH[1]}"
            has_tdd=false

            # Check if it's explicitly NO TDD
            if [[ "$line" =~ "NO TDD" ]] || [[ "$line" =~ "— NO TDD" ]]; then
                has_tdd=false
            fi
        fi

        # Check for TDD sections
        if [[ "$line" =~ ^###[[:space:]]+(Test[[:space:]]+Implementation|Test[[:space:]]+Design) ]]; then
            has_tdd=true
        fi
    done < "$tasks_file"

    # Save last phase
    if [[ -n "$current_phase" ]]; then
        phases+=("$current_phase:$has_tdd")
    fi

    echo "${phases[@]}"
}

# Copy template if not exists (idempotent)
copy_template_if_needed() {
    local src="$1"
    local dest="$2"
    local name="$3"

    if [[ ! -f "$src" ]]; then
        echo "Warning: Source template not found: $src" >&2
        return 1
    fi

    if [[ -f "$dest" ]]; then
        echo "Skipped: $name (already exists)" >&2
        echo "$name:skipped"
    else
        cp "$src" "$dest"
        echo "Created: $name" >&2
        echo "$name:created"
    fi
}

# Parse phases
PHASES_RAW=$(parse_phases "$TASKS_FILE")
PHASES=($PHASES_RAW)

TEMPLATES_CREATED=()
PHASES_JSON="["

for i in "${!PHASES[@]}"; do
    phase_info="${PHASES[$i]}"
    phase_num="${phase_info%%:*}"
    has_tdd="${phase_info##*:}"

    # Determine phase type
    if [[ "$phase_num" == "1" ]]; then
        phase_type="setup"
    elif [[ "$has_tdd" == "true" ]]; then
        phase_type="tdd"
    else
        phase_type="standard"
    fi

    # Create output file (directly with final name)
    if [[ "$phase_num" == "1" ]]; then
        # Phase 1 uses specific template
        result=$(copy_template_if_needed \
            "$TEMPLATE_SRC/ph1-output-template.md" \
            "$FEATURE_DIR/tasks/ph1-output.md" \
            "tasks/ph1-output.md")
        TEMPLATES_CREATED+=("$result")
    else
        # Phase N uses generic template
        result=$(copy_template_if_needed \
            "$TEMPLATE_SRC/phN-output-template.md" \
            "$FEATURE_DIR/tasks/ph${phase_num}-output.md" \
            "tasks/ph${phase_num}-output.md")
        TEMPLATES_CREATED+=("$result")
    fi

    # Create RED test template for TDD phases
    if [[ "$has_tdd" == "true" ]]; then
        result=$(copy_template_if_needed \
            "$TEMPLATE_SRC/red-test-template.md" \
            "$FEATURE_DIR/red-tests/ph${phase_num}-test-template.md" \
            "red-tests/ph${phase_num}-test-template.md")
        TEMPLATES_CREATED+=("$result")
    fi

    # Build JSON
    if [[ $i -gt 0 ]]; then
        PHASES_JSON+=","
    fi
    PHASES_JSON+="{\"number\":$phase_num,\"type\":\"$phase_type\",\"tdd\":$has_tdd}"
done

PHASES_JSON+="]"

# Build templates JSON array
TEMPLATES_JSON="["
for i in "${!TEMPLATES_CREATED[@]}"; do
    if [[ $i -gt 0 ]]; then
        TEMPLATES_JSON+=","
    fi
    TEMPLATES_JSON+="\"${TEMPLATES_CREATED[$i]}\""
done
TEMPLATES_JSON+="]"

# Output results
if $JSON_MODE; then
    printf '{"FEATURE_DIR":"%s","TASKS_FILE":"%s","PHASES":%s,"TEMPLATES":%s}\n' \
        "$FEATURE_DIR" "$TASKS_FILE" "$PHASES_JSON" "$TEMPLATES_JSON"
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "TASKS_FILE: $TASKS_FILE"
    echo "PHASES:"
    for phase_info in "${PHASES[@]}"; do
        phase_num="${phase_info%%:*}"
        has_tdd="${phase_info##*:}"
        echo "  - Phase $phase_num (TDD: $has_tdd)"
    done
    echo "TEMPLATES:"
    for template in "${TEMPLATES_CREATED[@]}"; do
        echo "  - $template"
    done
fi
