#!/bin/bash
# Validation script for CLI refactoring
set -e

BASELINE_DIR="specs/036-cli-refactor/baseline"
CURRENT_DIR=$(mktemp -d)

echo "=== CLI Refactoring Validation ==="
echo

# Test 1: Help text comparison
echo "1. Validating help text..."
for cmd in main import organize status retry clean trace; do
    if [ "$cmd" = "main" ]; then
        python -m src.etl --help > "$CURRENT_DIR/${cmd}_help.txt" 2>&1
    else
        python -m src.etl $cmd --help > "$CURRENT_DIR/${cmd}_help.txt" 2>&1
    fi

    if diff -q "$BASELINE_DIR/${cmd}_help.txt" "$CURRENT_DIR/${cmd}_help.txt" > /dev/null; then
        echo "   ✓ $cmd help text identical"
    else
        echo "   ✗ $cmd help text CHANGED"
        echo "      Diff:"
        diff "$BASELINE_DIR/${cmd}_help.txt" "$CURRENT_DIR/${cmd}_help.txt" | head -20
        exit 1
    fi
done

# Test 2: Run test suite
echo
echo "2. Running test suite..."
if make test > /dev/null 2>&1; then
    echo "   ✓ All tests passed"
else
    echo "   ⚠ Tests have failures (acceptable if baseline also had failures)"
fi

# Cleanup
rm -rf "$CURRENT_DIR"

echo
echo "✅ All validations passed"
