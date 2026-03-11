#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${BASE_DIR}/.venv/bin/python"
TEST_DATA_DIR="${BASE_DIR}/data/test"
FIXTURE_ZIP="${BASE_DIR}/tests/fixtures/claude_test.zip"

echo "Preparing test data..."
"${BASE_DIR}/scripts/prepare-test-dirs.sh" "$TEST_DATA_DIR" "$FIXTURE_ZIP"

echo "Running full pipeline..."
cd "$BASE_DIR" && KEDRO_ENV=test "$PYTHON" -m kedro run --env=test

echo "Comparing with golden files..."
if [ ! -d "${BASE_DIR}/tests/fixtures/golden" ] || [ "$(ls -1 "${BASE_DIR}/tests/fixtures/golden/"*.md 2>/dev/null | wc -l)" -eq 0 ]; then
    echo "Golden files not found. Run 'make test-e2e-update-golden' first."
    rm -rf "$TEST_DATA_DIR"
    exit 1
fi
cd "$BASE_DIR" && PYTHONPATH="${BASE_DIR}/src" "$PYTHON" -m tests.e2e.golden_comparator \
    --actual "$TEST_DATA_DIR/07_model_output/organized" \
    --golden "${BASE_DIR}/tests/fixtures/golden" \
    --threshold 0.8

echo "Cleaning up..."
rm -rf "$TEST_DATA_DIR"
echo "E2E test complete (golden file comparison passed)"
