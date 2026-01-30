#!/bin/bash
# Python Lint Hook for Claude Code
# Runs ruff lint and format on Python files after Edit/Write

# Debug log
LOG_FILE="/tmp/claude_hook_debug.log"
echo "=== Hook executed at $(date) ===" >> "$LOG_FILE"

# Read stdin and save it
INPUT=$(cat)
echo "$INPUT" >> "$LOG_FILE"

# Parse stdin JSON to get file_path and check if Python file
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path')
echo "FILE_PATH: $FILE_PATH" >> "$LOG_FILE"

# Early exit if not Python file
if [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# Run auto-fix and format on Python files
echo "🔧 Auto-fixing and formatting $FILE_PATH..."
cd "$CLAUDE_PROJECT_DIR" || exit 1

# Auto-fix lint issues
.venv/bin/ruff check --fix "$FILE_PATH" 2>&1

# Format code
.venv/bin/ruff format "$FILE_PATH" 2>&1

# Show remaining issues (if any)
echo "✅ Checking for remaining issues..."
.venv/bin/ruff check "$FILE_PATH" 2>&1 | head -10
